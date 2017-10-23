from copy import copy

import numpy as np

import simtk.openmm.app as omma
import simtk.openmm as omm
import simtk.unit as unit

from wepy.walker import Walker
from wepy.runner import Runner

# for the sim manager, dependencies will change
import sys
import os
from collections import namedtuple

import numpy as np
import pandas as pd
import h5py

from wepy.sim_manager import Manager

# default inputs
from wepy.resampling.resampler import NoResampler
from wepy.runner import NoRunner
from wepy.boundary_conditions.boundary import NoBC

GET_STATE_KWARG_DEFAULTS = (('getPositions', True),
                            ('getVelocities', True),
                            ('getForces', True),
                            ('getEnergy', True),
                            ('getParameters', True),
                            ('getParameterDerivatives', True),
                            ('enforcePeriodicBox', True),)
                            # TODO unsure of how to use this kwarg
                            #('groups') )



UNITS = (('positions_unit', unit.nanometer),
         ('time_unit', unit.picosecond),
         ('box_vectors_unit', unit.nanometer),
         ('velocities_unit', unit.nanometer/unit.picosecond),
         ('forces_unit', unit.kilojoule / (unit.nanometer * unit.mole)),
         ('box_volume_unit', unit.nanometer),
         ('kinetic_energy_unit', unit.kilojoule / unit.mole),
         ('potential_energy_unit', unit.kilojoule / unit.mole),
        )

UNIT_NAMES = (('positions_unit', unit.nanometer.get_name()),
         ('time_unit', unit.picosecond.get_name()),
         ('box_vectors_unit', unit.nanometer.get_name()),
         ('velocities_unit', (unit.nanometer/unit.picosecond).get_name()),
         ('forces_unit', (unit.kilojoule / (unit.nanometer * unit.mole)).get_name()),
         ('box_volume_unit', unit.nanometer.get_name()),
         ('kinetic_energy_unit', (unit.kilojoule / unit.mole).get_name()),
         ('potential_energy_unit', (unit.kilojoule / unit.mole).get_name()),
        )


class OpenMMRunner(Runner):

    def __init__(self, system, topology, integrator, platform=None):
        self.system = system
        self.topology = topology
        self.integrator = integrator
        self.platform_name = platform

    def run_segment(self, walker, segment_length, getState_kwargs=None, **kwargs):

        # set the kwargs that will be passed to getState
        tmp_getState_kwargs = getState_kwargs
        getState_kwargs = dict(GET_STATE_KWARG_DEFAULTS)
        if tmp_getState_kwargs is not None:
            getState_kwargs.update(tmp_getState_kwargs)

        # if a platform was given we use it to make a Simulation object
        if self.platform_name is not None:
            # get the platform by its name to use
            platform = omm.Platform.getPlatformByName(self.platform_name)
            # set properties from the kwargs if they apply to the platform
            for key, value in kwargs.items():
                if key in platform.getPropertyNames():
                    platform.setPropertyDefaultValue(key, value)

            # instantiate a simulation object
            simulation = omma.Simulation(self.topology, self.system,
                                         copy(self.integrator), platform)
        # otherwise just use the default or environmentally defined one
        else:
            simulation = omma.Simulation(self.topology, self.system,
                                         copy(self.integrator))

        # set the state to the context from the walker
        simulation.context.setState(walker.state)

        # Run the simulation segment for the number of time steps
        simulation.step(segment_length)

        # save the state of the system with all possible values
        new_state = simulation.context.getState(**getState_kwargs)

        # create a new walker for this
        new_walker = OpenMMWalker(new_state, walker.weight)

        return new_walker


class OpenMMWalker(Walker):

    def __init__(self, state, weight):
        super().__init__(state, weight)

        self._keys = ['positions', 'velocities', 'forces', 'kinetic_energy',
                      'potential_energy', 'time', 'box_vectors', 'box_volume',
                      'parameters', 'parameter_derivatives']

    def dict(self):
        """return a dict of the values."""
        return {'positions' : self.positions_values(),
                'velocities' : self.velocities_values(),
                'forces' : self.forces_values(),
                'kinetic_energy' : self.kinetic_energy_value(),
                'potential_energy' : self.potential_energy_value(),
                'time' : self.time_value(),
                'box_vectors' : self.box_vectors_values(),
                'box_volume' : self.box_volume_value(),
                'parameters' : self.parameters_values(),
                'parameter_derivatives' : self.parameter_derivatives_values()
                    }

    def keys(self):
        return self._keys

    def __getitem__(self, key):
        if key == 'positions':
            return self.positions_values()
        elif key == 'velocities':
            return self.velocities_values
        elif key == 'forces':
            return self.forces_values()
        elif key == 'kinetic_energy':
            return self.kinetic_energy_value()
        elif key == 'potential_energy':
            return self.potential_energy_value()
        elif key == 'time':
            return self.time_value()
        elif key == 'box_vectors':
            return self.box_vectors_values()
        elif key == 'box_volume':
            return self.box_volume_value()
        elif key == 'parameters':
            return self.parameters_values()
        elif key == 'parameter_derivatives':
            return self.parameter_derivatives_values()
        else:
            raise KeyError('{} not an OpenMMWalker attribute')

    @property
    def positions(self):
        try:
            return self.state.getPositions()
        except TypeError:
            return None

    @property
    def positions_unit(self):
        return self.positions.unit

    def positions_values(self):
        return np.array(self.positions.value_in_unit(self.positions_unit))

    @property
    def velocities(self):
        try:
            return self.state.getVelocities()
        except TypeError:
            return None

    @property
    def velocities_unit(self):
        return self.velocities.unit

    def velocities_values(self):
        velocities = self.velocities
        if velocities is None:
            return None
        else:
            return np.array(self.velocities.value_in_unit(self.velocities_unit))

    @property
    def forces(self):
        try:
            return self.state.getForces()
        except TypeError:
            return None

    @property
    def forces_unit(self):
        return self.forces.unit

    def forces_values(self):
        forces = self.forces
        if forces is None:
            return None
        else:
            return np.array(self.forces.value_in_unit(self.forces_unit))

    @property
    def kinetic_energy(self):
        try:
            return self.state.getKineticEnergy()
        except TypeError:
            return None

    @property
    def kinetic_energy_unit(self):
        return self.kinetic_energy.unit

    def kinetic_energy_value(self):
        kinetic_energy = self.kinetic_energy
        if kinetic_energy is None:
            return None
        else:
            return np.array([self.kinetic_energy.value_in_unit(self.kinetic_energy_unit)])

    @property
    def potential_energy(self):
        try:
            return self.state.getPotentialEnergy()
        except TypeError:
            return None

    @property
    def potential_energy_unit(self):
        return self.potential_energy.unit

    def potential_energy_value(self):
        potential_energy = self.potential_energy
        if potential_energy is None:
            return None
        else:
            return np.array([self.potential_energy.value_in_unit(self.potential_energy_unit)])

    @property
    def time(self):
        try:
            return self.state.getTime()
        except TypeError:
            return None

    @property
    def time_unit(self):
        return self.time.unit

    def time_value(self):
        time = self.time
        if time is None:
            return None
        else:
            return np.array([self.time.value_in_unit(self.time_unit)])

    @property
    def box_vectors(self):
        try:
            return self.state.getPeriodicBoxVectors()
        except TypeError:
            return None

    @property
    def box_vectors_unit(self):
        return self.box_vectors.unit

    def box_vectors_values(self):
        box_vectors = self.box_vectors
        if box_vectors is None:
            return None
        else:
            return np.array(self.box_vectors.value_in_unit(self.box_vectors_unit))

    @property
    def box_volume(self):
        try:
            return self.state.getPeriodicBoxVolume()
        except TypeError:
            return None

    @property
    def box_volume_unit(self):
        return self.box_volume.unit

    def box_volume_value(self):
        box_volume = self.box_volume
        if box_volume is None:
            return None
        else:
            return np.array([self.box_volume.value_in_unit(self.box_volume_unit)])

    @property
    def parameters(self):
        try:
            return self.state.getParameters()
        except TypeError:
            return None

    # TODO test this, this is jsut a guess because I don't use parameters
    @property
    def parameters_unit(self):
        param_units = {key : val.unit for key, val in self.parameters.items()}
        return param_units

    # TODO test this, this is jsut a guess because I don't use parameters
    def parameters_values(self):
        if self.parameters is None:
            return None

        param_arrs = {key : np.array(val.value_in_unit(val.unit)) for key, val
                          in self.parameters.items()}

        # return None if there is nothing in this
        if len(param_arrs) == 0:
            return None
        else:
            return param_arrs

    @property
    def parameter_derivatives(self):
        try:
            return self.state.getEnergyParameterDerivatives()
        except TypeError:
            return None

    # TODO test this, this is jsut a guess because I don't use parameters
    @property
    def parameter_derivatives_unit(self):
        param_units = {key : val.unit for key, val in self.parameter_derivatives.items()}
        return param_units

    # TODO test this, this is jsut a guess because I don't use parameter_derivatives
    def parameter_derivatives_values(self):

        if self.parameter_derivatives is None:
            return None

        param_arrs = {key : np.array(val.value_in_unit(val.unit)) for key, val
                          in self.parameter_derivatives.items()}

        # return None if there is nothing in this
        if len(param_arrs) == 0:
            return None
        else:
            return param_arrs

    def to_mdtraj(self):
        """ Returns an mdtraj.Trajectory object from this walker's state."""
        raise NotImplementedError
        import mdtraj as mdj
        # resize the time to a 1D vector
        return mdj.Trajectory(self.positions_values,
                              time=self.time_value[:,0], unitcell_vectors=self.box_vectors)
