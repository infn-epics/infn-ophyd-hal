"""
ChannelFinder REST client for querying PV metadata.

Provides a lightweight client to search channels, retrieve properties,
and discover PV prefixes from a ChannelFinder service instance.

The ChannelFinder REST API base is typically:
    ``http://<host>:<port>/ChannelFinder/resources``

Endpoints used:
    GET /channels                — search channels by query parameters
    GET /channels/{channelName}  — get single channel by name
    GET /channels/count          — count matching channels
    GET /properties              — list all properties
    GET /tags                    — list all tags
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class ChannelFinderClient:
    """REST client for the ChannelFinder service.

    Parameters
    ----------
    url : str
        Base URL of the ChannelFinder service, e.g.
        ``http://channelfinder.example.com:8080/ChannelFinder``.
    timeout : float
        Default request timeout in seconds.
    auth : tuple, optional
        (username, password) for basic-auth protected endpoints.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 10.0,
        auth: Optional[tuple] = None,
    ):
        self.base_url = url.rstrip("/")
        self.timeout = timeout
        self.auth = auth
        self._session = requests.Session()
        if auth:
            self._session.auth = auth

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        url = f"{self.base_url}/resources/{path}"
        resp = self._session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Channel queries
    # ------------------------------------------------------------------

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        """Search channels using ChannelFinder query parameters.

        Common parameters (prefix with ``~`` in the API, added here automatically):
            name : str — channel name pattern (glob), e.g. ``SPARC*``
            tag  : str — tag filter
            size : int — max results
            from_ : int — pagination offset (note trailing underscore to avoid
                          shadowing Python ``from``)

        Any other keyword is treated as a property filter, e.g.
        ``iocName='tml-ch1'``.

        Returns a list of channel dicts::

            [{"name": "SPARC:MOT:TML:GUNFLG01:RBV",
              "owner": "admin",
              "properties": [{"name": "iocName", "value": "tml-ch1"}, ...],
              "tags": [...]}, ...]
        """
        params: Dict[str, str] = {}
        for key, value in kwargs.items():
            if key == "from_":
                params["~from"] = str(value)
            elif key in ("name", "tag", "size"):
                params[f"~{key}"] = str(value)
            else:
                params[key] = str(value)
        return self._get("channels", params=params)

    def get_channel(self, channel_name: str) -> Dict[str, Any]:
        """Retrieve a single channel by exact name.

        Raises ``requests.HTTPError`` (404) if not found.
        """
        return self._get(f"channels/{channel_name}")

    def count(self, **kwargs) -> int:
        """Return the number of channels matching the given filters.

        Accepts the same keyword arguments as :meth:`search`.
        """
        params: Dict[str, str] = {}
        for key, value in kwargs.items():
            if key == "from_":
                params["~from"] = str(value)
            elif key in ("name", "tag", "size"):
                params[f"~{key}"] = str(value)
            else:
                params[key] = str(value)
        return self._get("channels/count", params=params)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_channels_by_ioc(self, ioc_name: str, **kwargs) -> List[Dict[str, Any]]:
        """Return all channels belonging to a specific IOC.

        Uses the ``iocName`` property filter.
        """
        return self.search(iocName=ioc_name, **kwargs)

    def get_channels_by_prefix(self, prefix: str, **kwargs) -> List[Dict[str, Any]]:
        """Return channels whose name starts with *prefix*.

        Appends ``*`` to the prefix for glob matching.
        """
        pattern = prefix if prefix.endswith("*") else f"{prefix}*"
        return self.search(name=pattern, **kwargs)

    def get_channels_by_devgroup(self, devgroup: str, **kwargs) -> List[Dict[str, Any]]:
        """Return channels tagged with a specific device group."""
        return self.search(devgroup=devgroup, **kwargs)

    def get_channel_properties(self, channel_name: str) -> Dict[str, str]:
        """Return a flat ``{property_name: value}`` dict for a channel."""
        ch = self.get_channel(channel_name)
        return {
            p["name"]: p.get("value", "")
            for p in ch.get("properties", [])
        }

    def list_properties(self) -> List[Dict[str, Any]]:
        """List all registered properties."""
        return self._get("properties")

    def list_tags(self) -> List[Dict[str, Any]]:
        """List all registered tags."""
        return self._get("tags")

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    def discover_devices(
        self,
        ioc_name: Optional[str] = None,
        devgroup: Optional[str] = None,
        name_pattern: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Discover devices from ChannelFinder metadata.

        Searches for channels and groups them into device descriptors
        based on their properties (``iocName``, ``devgroup``, ``devtype``,
        ``iocprefix``).

        Returns a list of device dicts suitable for use with
        :class:`DeviceFactory`::

            [{"name": "GUNFLG01",
              "devgroup": "mot",
              "devtype": "technosoft-asyn",
              "prefix": "SPARC:MOT:TML:GUNFLG01",
              "iocname": "tml-ch1",
              "properties": {...}}, ...]
        """
        kwargs = {}
        if ioc_name:
            kwargs["iocName"] = ioc_name
        if devgroup:
            kwargs["devgroup"] = devgroup
        if name_pattern:
            kwargs["name"] = name_pattern

        channels = self.search(**kwargs)

        # Group channels by their stem (PV name without the field/suffix)
        devices: Dict[str, Dict[str, Any]] = {}
        for ch in channels:
            props = {p["name"]: p.get("value", "") for p in ch.get("properties", [])}
            pv_name = ch.get("name", "")

            # Extract device name: last segment before the record-field part
            # e.g. SPARC:MOT:TML:GUNFLG01:RBV -> GUNFLG01
            parts = pv_name.split(":")
            if len(parts) >= 2:
                device_stem = parts[-2]
                pv_prefix = ":".join(parts[:-1])
            else:
                device_stem = pv_name
                pv_prefix = pv_name

            if device_stem not in devices:
                devices[device_stem] = {
                    "name": device_stem,
                    "devgroup": props.get("devgroup", ""),
                    "devtype": props.get("devtype", ""),
                    "prefix": pv_prefix,
                    "iocname": props.get("iocName", ""),
                    "template": props.get("template", ""),
                    "properties": props,
                    "pvs": [],
                }
            devices[device_stem]["pvs"].append(pv_name)

        return list(devices.values())

    # ------------------------------------------------------------------
    # Connection check
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the ChannelFinder service is reachable."""
        try:
            self._session.get(
                f"{self.base_url}",
                timeout=self.timeout,
            )
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False
