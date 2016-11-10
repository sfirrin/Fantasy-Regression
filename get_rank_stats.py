import data_sanitizer
import numpy


def get_median_rank_scores(position_players):
    rank_medians = {}
    rank_points = {}

    for rank in range(1, 51):
        points_at_rank = [player.actual_points for player in position_players if player.actual_rank == rank]
        median_at_rank = numpy.nanmedian(points_at_rank)
        # print(rank, median_at_rank)
        # print(points_at_rank)
        rank_medians[rank] = median_at_rank
        rank_points[rank] = points_at_rank

    return rank_medians, rank_points


weeks = data_sanitizer.get_all_weeks()

all_qbs = []
all_rbs = []
all_wrs = []
all_tes = []
all_flexes = []
all_dsts = []

for week in weeks:
    all_qbs += week.qbs
    all_rbs += week.rbs
    all_wrs += week.wrs
    all_tes += week.tes
    all_flexes += week.flexes
    all_dsts += week.dsts

qb_medians, qb_rank_points = get_median_rank_scores(all_qbs)
rb_medians, rb_rank_points = get_median_rank_scores(all_rbs)
wr_medians, wr_rank_points = get_median_rank_scores(all_wrs)
te_medians, te_rank_points = get_median_rank_scores(all_tes)
flex_medians, flex_rank_points = get_median_rank_scores(all_flexes)
dst_medians, dst_rank_points = get_median_rank_scores(all_dsts)

