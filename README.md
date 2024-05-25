# infn_ophyd_hal

A package for HardawareAbstractionLayer of Devices used in the INFN Facilities.
The HAL will drammatically simplify:

- High Level Scientific applications 
- Implementation of generic IOCs
- Implementation of GUIs

## Installation


```bash
pip install infn_ophyd_hal
```
## Usage

```

```
### Environment
python3.10 -m venv ophyd-env
source ophyd-env/bin/activate
pip install -e .
### Package
pip install wheel
pip install twine
python setup.py sdist bdist_wheel
twine upload dist/*


