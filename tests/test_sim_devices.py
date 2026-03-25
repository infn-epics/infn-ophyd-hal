"""Tests for sim devices — runs without live EPICS IOCs."""

import pytest
from infn_ophyd_hal import DeviceFactory, OphydMotorSim
from infn_ophyd_hal.sim_devices import (
    OphydBpmSim, OphydDISim, OphydDOSim, OphydAISim, OphydAOSim,
    OphydRTDSim, OphydVPCSim, OphydVGCSim,
)


# -----------------------------------------------------------------------
# DeviceFactory integration
# -----------------------------------------------------------------------

class TestDeviceFactory:
    def test_factory_creates_motor_sim(self, factory):
        dev = factory.create_device('mot', 'sim', 'SIM:MOT', 'my_motor')
        assert isinstance(dev, OphydMotorSim)

    def test_factory_creates_bpm_sim(self, factory):
        dev = factory.create_device('diag', 'sim', 'SIM:BPM', 'my_bpm')
        assert isinstance(dev, OphydBpmSim)

    def test_factory_creates_vpc_sim(self, factory):
        dev = factory.create_device('vac', 'sim', 'SIM:VPC', 'my_vpc')
        assert isinstance(dev, OphydVPCSim)

    def test_factory_creates_io_sim(self, factory):
        for subtype, cls in [
            ('sim-di', OphydDISim), ('sim-do', OphydDOSim),
            ('sim-ai', OphydAISim), ('sim-ao', OphydAOSim),
            ('sim-rtd', OphydRTDSim),
        ]:
            dev = factory.create_device('io', subtype, 'SIM:IO', f'my_{subtype}')
            assert isinstance(dev, cls), f"Expected {cls.__name__} for {subtype}"

    def test_factory_generic_mot_is_asyn(self, factory):
        """devtype='generic' for mot group must resolve to the asyn motor class."""
        from infn_ophyd_hal.asyn_ophyd_motor import OphydAsynMotor
        cls = factory._device_map.get(('mot', 'generic'))
        assert cls is OphydAsynMotor

    def test_factory_unknown_type_returns_none(self, factory):
        dev = factory.create_device('unknown', 'nope', 'SIM', 'nothing')
        assert dev is None

    def test_supported_types_not_empty(self, factory):
        types = factory.get_supported_types()
        assert len(types) > 0


# -----------------------------------------------------------------------
# Motor Sim
# -----------------------------------------------------------------------

class TestMotorSim:
    def test_initial_position(self, motor_sim):
        assert motor_sim.position == 0.0

    def test_move(self, motor_sim):
        motor_sim.move(50.0)
        assert motor_sim.position == 50.0
        assert not motor_sim.moving

    def test_limits(self, motor_sim):
        assert motor_sim.limits == (-200, 200)

    def test_check_value_within_limits(self, motor_sim):
        motor_sim.check_value(100)  # should not raise

    def test_check_value_above_limit(self, motor_sim):
        with pytest.raises(ValueError):
            motor_sim.check_value(300)

    def test_check_value_below_limit(self, motor_sim):
        with pytest.raises(ValueError):
            motor_sim.check_value(-300)

    def test_move_poi(self, motor_sim):
        motor_sim.move('sample')
        assert motor_sim.position == 100

    def test_poi2pos(self, motor_sim):
        assert motor_sim.poi2pos('home') == 0
        assert motor_sim.poi2pos('sample') == 100
        assert motor_sim.poi2pos('nonexistent') == -1000

    def test_pos2poi(self, motor_sim):
        motor_sim.move(0)
        assert motor_sim.pos2poi(0) == 'home'

    def test_home(self, motor_sim):
        motor_sim.move(42.0)
        motor_sim.home()
        assert motor_sim.position == 0.0

    def test_stop(self, motor_sim):
        motor_sim.stop()
        assert not motor_sim.moving

    def test_egu(self, motor_sim):
        assert motor_sim.egu == 'mm'

    def test_precision(self, motor_sim):
        assert motor_sim.precision == 3

    def test_read(self, motor_sim):
        motor_sim.move(10.0)
        data = motor_sim.read()
        assert data['test_motor']['value'] == 10.0

    def test_describe(self, motor_sim):
        desc = motor_sim.describe()
        assert 'test_motor' in desc

    def test_get_pos(self, motor_sim):
        motor_sim.move(100)
        assert motor_sim.get_pos() == 100
        result = motor_sim.get_pos(poi=True)
        assert result['name'] == 'sample'


# -----------------------------------------------------------------------
# BPM Sim
# -----------------------------------------------------------------------

class TestBpmSim:
    def test_initial_values(self, bpm_sim):
        assert bpm_sim.x == 0.0
        assert bpm_sim.y == 0.0
        assert bpm_sim.sum == 100.0

    def test_read_returns_values(self, bpm_sim):
        data = bpm_sim.read()
        assert 'test_bpm_x' in data
        assert 'test_bpm_y' in data

    def test_thsld(self, bpm_sim):
        bpm_sim.thsld(0.8)
        assert bpm_sim._threshold == 0.8

    def test_reset(self, bpm_sim):
        bpm_sim.read()  # randomize
        bpm_sim.reset()
        assert bpm_sim.x == 0.0
        assert bpm_sim.y == 0.0

    def test_describe(self, bpm_sim):
        desc = bpm_sim.describe()
        assert 'test_bpm_x' in desc

    def test_stage_unstage(self, bpm_sim):
        bpm_sim.stage()
        bpm_sim.unstage()


# -----------------------------------------------------------------------
# IO Sims
# -----------------------------------------------------------------------

class TestDISim:
    def test_initial_value(self, di_sim):
        assert di_sim.get() == 0

    def test_set_sim_value(self, di_sim):
        di_sim.set_sim_value(1)
        assert di_sim.get() == 1

    def test_read(self, di_sim):
        data = di_sim.read()
        assert data['test_di']['value'] == 0


class TestDOSim:
    def test_initial_value(self, do_sim):
        assert do_sim.get() == 0

    def test_set(self, do_sim):
        do_sim.set(1)
        assert do_sim.get() == 1


class TestAISim:
    def test_initial_value(self, ai_sim):
        assert ai_sim.get() == 0.0

    def test_set_sim_value(self, ai_sim):
        ai_sim.set_sim_value(3.14)
        assert ai_sim.get() == pytest.approx(3.14)


class TestAOSim:
    def test_initial_value(self, ao_sim):
        assert ao_sim.get() == 0.0

    def test_set(self, ao_sim):
        ao_sim.set(2.71)
        assert ao_sim.get() == pytest.approx(2.71)


class TestRTDSim:
    def test_read(self, rtd_sim):
        data = rtd_sim.read()
        assert data['test_rtd']['value'] == pytest.approx(25.0)


# -----------------------------------------------------------------------
# Vacuum Sims
# -----------------------------------------------------------------------

class TestVPCSim:
    def test_read(self, vpc_sim):
        data = vpc_sim.read()
        assert data['test_vpc']['value'] > 0

    def test_describe(self, vpc_sim):
        desc = vpc_sim.describe()
        assert 'test_vpc' in desc


class TestVGCSim:
    def test_read(self, vgc_sim):
        data = vgc_sim.read()
        assert data['test_vgc']['value'] > 0

    def test_describe(self, vgc_sim):
        desc = vgc_sim.describe()
        assert 'test_vgc' in desc
