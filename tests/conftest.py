"""Pytest fixtures for sim-device tests."""

import pytest
from infn_ophyd_hal import (
    DeviceFactory,
    OphydMotorSim,
    OphydPSSim,
)
from infn_ophyd_hal.sim_devices import (
    OphydBpmSim,
    OphydDISim,
    OphydDOSim,
    OphydAISim,
    OphydAOSim,
    OphydRTDSim,
    OphydVPCSim,
    OphydVGCSim,
)


@pytest.fixture
def factory():
    return DeviceFactory()


@pytest.fixture
def motor_sim():
    return OphydMotorSim(
        prefix="SIM:MOT",
        name="test_motor",
        poi=[{"name": "home", "pos": 0}, {"name": "sample", "pos": 100}],
        config={"motor": {"dllm": -200, "dhlm": 200}},
    )


@pytest.fixture
def bpm_sim():
    return OphydBpmSim(prefix="SIM:BPM", name="test_bpm")


@pytest.fixture
def ps_sim():
    return OphydPSSim(name="test_ps", uncertainty_percentage=0, simcycle=0.05)


@pytest.fixture
def di_sim():
    return OphydDISim(prefix="SIM:DI", name="test_di")


@pytest.fixture
def do_sim():
    return OphydDOSim(prefix="SIM:DO", name="test_do")


@pytest.fixture
def ai_sim():
    return OphydAISim(prefix="SIM:AI", name="test_ai", noise=0)


@pytest.fixture
def ao_sim():
    return OphydAOSim(prefix="SIM:AO", name="test_ao")


@pytest.fixture
def rtd_sim():
    return OphydRTDSim(prefix="SIM:RTD", name="test_rtd", base_temp=25.0, noise=0)


@pytest.fixture
def vpc_sim():
    return OphydVPCSim(prefix="SIM:VPC", name="test_vpc", base_pressure=1e-7)


@pytest.fixture
def vgc_sim():
    return OphydVGCSim(prefix="SIM:VGC", name="test_vgc", base_pressure=1e-5)
