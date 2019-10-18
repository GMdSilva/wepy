import os.path as osp
from collections import defaultdict
import itertools as it
import logging

from wepy.resampling.decisions.clone_merge import MultiCloneMergeDecision
from wepy.reporter.dashboard import ResamplerDashboardSection

import numpy as np
import pandas as pd

class REVODashboardSection(ResamplerDashboardSection):

    RESAMPLER_TEMPLATE = \
"""

Resampling Algorithm: REVO

Distance Exponent: {{ dist_exponent }}
Characteristic Distance: {{ char_dist }}
Merge Distance: {{ merge_dist }}

** Resamplig
Cycle index: {{ cycle_idx }}
The percentage of cloned walkers: {{ percentage_cloned_walkers }} %
The percentage of merged walkers: {{ percentage_merged_walkers }} %

** Statistics
Average All to All Distance: {{ avg_distance }}
Minimum All to All Distance: {{ min_distance }}
Maximum All to All Distance: {{ max_distance }}
Variation value = {{ variation }}
"""

    def __init__(self, resampler):

        super().__init__(resampler)

        self.dist_exponent = resampler.dist_exponent
        self.merge_dist = resampler.merge_dist
        self.lpmin = resampler.lpmin
        self.char_dist = resampler.char_dist
        self.seed = resampler.seed
        self.decision = resampler.DECISION

        # updatables
        self.percentage_cloned_walkers = 0
        self.percentage_merged_walkers = 0
        #REVO
        self.avg_distance = None
        self.min_distance = None
        self.max_distance = None
        self.variation_values = None

    def update_values(self, **kwargs):

        num_clones = 0
        num_merges = 0
        num_walkers = len(kwargs['resampling_data'])
        for walker_record in kwargs['resampling_data']:
            if walker_record['decision_id'][0]==self.decision.ENUM.CLONE.value:
                num_clones += 1
            elif walker_record['decision_id'][0]==self.decision.ENUM.KEEP_MERGE.value:
                num_merges += 1

        self.percentage_cloned_walkers = (num_clones/num_walkers) * 100
        self.percentage_merged_walkers = (num_merges/num_walkers) * 100

        #Get the statistics
        for resampler_record in kwargs['resampler_data']:
            self.variation_value = resampler_record['variation'][0]
            distance_matrix = resampler_record['distance_matrix']


        #get the upper triangle values of the distance_matrix
        distance_matrix = np.triu(distance_matrix)
        distance_values= distance_matrix[np.where(distance_matrix>0)]
        self.avg_distance = np.average(distance_values)
        self.min_distance = np.min(distance_values)
        self.max_distance  = np.max(distance_values)

        self.cycle_idx = kwargs['cycle_idx']

    def gen_fields(self, **kwargs):

        fields = {
            'dist_exponent' : self.dist_exponent,
            'char_dist' : self.char_dist,
            'merge_dist' : self.merge_dist,
            'cycle_idx' : self.cycle_idx,
            'percentage_cloned_walkers' : self.percentage_cloned_walkers,
            'percentage_merged_walkers' : self.percentage_merged_walkers,
            'avg_distance' : self.avg_distance,
            'min_distance' : self.min_distance,
            'max_distance' : self.max_distance,
            'variation' : self.variation_value
        }

        return fields


# class REVODashboardReporter(DashboardReporter):
#     """ """

#     SUGGESTED_EXTENSIONS = ("revo.dash.org",)
#     RESAMPLER_TEMPLATE = \
# """* REVO
# Distance Exponent: {dist_exponent}
# Characteristic Distance: {char_dist}
# Merge Distance: {merge_dist}
# ** Resamplig
# Cycle index: {cycle_idx}
# The percentage of cloned walkers: {percentage_cloned_walkers} %
# The percentage of merged walkers: {percentage_merged_walkers} %
# ** Statistics
# Average All to All Distance: {avg_distance}
# Minimum All to All Distance: {min_distance}
# Maximum All to All Distance: {max_distance}
# Variation value = {variation}
# """

#     def __init__(self,
#                  dist_exponent=None,
#                  merge_dist=None,
#                  char_dist=None,
#                  step_time=None, # seconds
#                  bc_cutoff_distance=None,
#                  **kwargs
#                 ):
#         """Constructor for the REVO dashboard reporter.

#         Parameters
#         ----------
#         dist_exponent : int
#           The distance exponent that modifies distance and weight novelty
#           relative to each other in the variation equation.

#         merge_dist : float
#             The merge distance threshold. Its value depends on the system
#             of interest.

#         char_dist : float
#             The characteristic distance value. It is calculated by running
#             a single dynamic cycle and then calculating the average distance
#             between all walkers.

#         step_time : float
#             The length of the time in each dynamics step.

#         bc_cutoff_distance : float
#             The distance for which a walker will be warped.

#         """

#         super().__init__(step_time, bc_cutoff_distance, **kwargs)

#         assert dist_exponent is not None, "Distance exponent must be given"
#         self.dist_exponent = dist_exponent

#         assert merge_dist is not None, "Merge distance must be given"
#         self.merge_dist = dist_exponent

#         assert char_dist is not None, "Characteristic distance must be given"
#         self.char_dist = char_dist

#         #Resamplig
#         self.decision = MultiCloneMergeDecision
#         self.percentage_cloned_walkers = 0
#         self.percentage_merged_walkers = 0
#         #REVO
#         self.avg_distance = None
#         self.min_distance = None
#         self.max_distance = None
#         self.variation_values = None


#     def _update_resampler_values(self, cycle_idx, resampling_data,  resampler_data):

#         """Update values associated with the REVO resampler.

#         Parameters
#         ----------
#         cycle_idx : int
#             The index of the last completed cycle.

#         resampling_data : list of dict of str : value
#             List of records specifying the resampling to occur at this
#             cycle.

#         resampler_data : list of dict of str : value
#             List of records specifying the changes to the state of the
#             resampler in the last cycle.

#         """

#         num_clones = 0
#         num_merges = 0
#         num_walkers = len(resampling_data)
#         for walker_record in resampling_data:
#             if walker_record['decision_id'][0]==self.decision.ENUM.CLONE.value:
#                 num_clones += 1
#             elif walker_record['decision_id'][0]==self.decision.ENUM.KEEP_MERGE.value:
#                 num_merges += 1

#         self.percentage_cloned_walkers = (num_clones/num_walkers) * 100
#         self.percentage_merged_walkers = (num_merges/num_walkers) * 100

#         #Get the statistics
#         for resampler_record in resampler_data:
#             self.variation_value = resampler_record['variation'][0]
#             distance_matrix = resampler_record['distance_matrix']


#         #get the upper triangle values of the distance_matrix
#         distance_matrix = np.triu(distance_matrix)
#         distance_values= distance_matrix[np.where(distance_matrix>0)]
#         self.avg_distance = np.average(distance_values)
#         self.min_distance = np.min(distance_values)
#         self.max_distance  = np.max(distance_values)

#         self.cycle_idx = cycle_idx

#     def _resampler_string(self):

#         resampler_string = self.RESAMPLER_TEMPLATE.format(
#             dist_exponent = self.dist_exponent,
#             char_dist = self.char_dist,
#             merge_dist = self.merge_dist,
#             cycle_idx = self.cycle_idx,
#             percentage_cloned_walkers=self.percentage_cloned_walkers,
#             percentage_merged_walkers=self.percentage_merged_walkers,
#             avg_distance = self.avg_distance,
#             min_distance = self.min_distance,
#             max_distance = self.max_distance,
#             variation = self.variation_value
#         )

#         return resampler_string
