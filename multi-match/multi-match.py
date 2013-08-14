import cv2
import math
import numpy as np
import sys

import stbt


def _confirm_match_template(image, template, match_parameters):
    if match_parameters.confirm_method == "normed-absdiff":
        cv2.normalize(image, image, 0, 255, cv2.NORM_MINMAX)
        cv2.normalize(template, template, 0, 255, cv2.NORM_MINMAX)

    absdiff = cv2.absdiff(image, template)
    _, thresholded = cv2.threshold(
        absdiff, int(match_parameters.confirm_threshold * 255),
        255, cv2.THRESH_BINARY)
    eroded = cv2.erode(
        thresholded,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        iterations=match_parameters.erode_passes)

    return (cv2.countNonZero(eroded) == 0)


def overlapping(p1, p2, boundary):
    """ Determines whether 2 points are within a certain
    (x, y) boundary of each other.

    `p1`, `p2` and boundary are all (x, y) tuples
    >>> overlapping((5, 5), (7, 6), (3, 3))
    True
    >>> overlapping((5, 5), (9, 9), (3, 3))
    False
    """
    return ((math.fabs(p1[0] - p2[0]) <= boundary[0]) and \
             math.fabs(p1[1] - p2[1]) <= boundary[1])


def cluster_point(point, clusters, boundary):
    """ Attempts to attach a point to a list of clusters of point
    given a boundary size. If the point does not belong to any
    existing cluster then a new one is created and appended.

    `point` is an (x, y) tuple
    `clusters` is a (possibly empty) list of clusters
    `boundary` is an (x, y) tuple

    Returns the updated `clusters` list
    >>> cluster_point((2, 4), [], (10, 10))
    [[(2, 4)]]
    >>> cluster_point((5, 6), [[(2, 4)]], (10, 10))
    [[(2, 4), (5, 6)]]
    >>> cluster_point((20, 20), [[(2, 4), (5, 6)]], (10, 10))
    [[(2, 4), (5, 6)], [(20, 20)]]
    """
    for i, cluster in enumerate(clusters):
        for p in cluster:
            if overlapping(point, p, boundary):
                clusters[i].append(point)
                return clusters
    clusters.append([point])
    return clusters


def strongest_match_from_clusters(heatmap, clusters):
    """ Reduces each cluster in the list of clusters down to a single point
    which corresponds to the strongest match location for that cluster.

    `heatmap` is a numpy or cv2 array
    `clusters` is a list of clustered points
    """
    match_points = []
    for cluster in clusters:
        strongest_result = 0
        for p in cluster:
            if heatmap[p[1]][p[0]] > strongest_result:
                strongest_result = heatmap[p[1]][p[0]]
                strongest_point = p
        match_points.append((strongest_point, strongest_result))
    return match_points


def crop_to_ROI(source, tlc, size):
    return source[
            tlc[1]:(tlc[1] + size[1]),
            tlc[0]:(tlc[0] + size[0])]


def multi_match(source, template, cutoff):
    """ Performs templatematching against source for every strong match
    location (not just the strongest).

    `source` and `template` are images loaded by OpenCV (numpy arrays)
    `cutoff` is a float [0.0..1.0] which represents the leeway to give when
    considering points as possible match locations, where a cutoff of 0.95
    means that only match locations with a strength of at least 95% that of
    the strongest match are considered.
    """

    # container to return all results in
    match_results = []

    heatmap = cv2.matchTemplate(source, template, cv2.TM_CCORR_NORMED)
    show(heatmap)
    _l, maxVal, _, maxLoc = cv2.minMaxLoc(heatmap)

    matched = False
    if maxVal <= 0.80:
        print "No matches"
    else:
        # confirm strongest match
        t_size = (template.shape[1], template.shape[0])
        roi = crop_to_ROI(source, maxLoc, t_size)
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        mp = stbt.MatchParameters(
                match_method="ccorr-normed", confirm_method="normed-absiff",
                confirm_threshold=0.2)

        matched = _confirm_match_template(
                roi_gray, template_gray, match_parameters=mp)

    if not matched:
        print "No matches."

    else:
        _, heatmap_thresh = cv2.threshold(
                heatmap, (maxVal * cutoff), 0, cv2.THRESH_TOZERO)
        show(heatmap_thresh)

        whites = [(x, y) \
                for (y, x) in np.transpose(np.nonzero(heatmap_thresh))]
        print len(whites), "white pixels found"
        if len(whites) > 1000:
            print ("Too many possible match points! This is going to take a "
                    "long time to cluster.\nConsider increasing the `cutoff` "
                    "value or making a better template!")
            sys.exit(0)

        clusters = []
        for px in whites:
            clusters = cluster_point(px, clusters, t_size)
        print len(clusters), "clusters found"
        match_locs = strongest_match_from_clusters(heatmap, clusters)

        for point, strength in match_locs:
            roi = crop_to_ROI(source, point, t_size)
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            matched = _confirm_match_template(roi_gray, template_gray, mp)
            match_results.append((matched, point, strength))

    return match_results


def draw_bound(matched, loc, size, frame):
    """ Returns frame with the bounding box of the result drawn on it."""
    _RED = [0, 0, 255]
    _GREEN = [0, 255, 0]
    cv2.rectangle(
            frame, (loc), (loc[0] + size[0], loc[1] + size[1]),
            _GREEN if matched else _RED, thickness=2)
    return frame


# display images
cv2.namedWindow('W')


def show(image):
    cv2.imshow('W', image)
    cv2.waitKey(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = cv2.imread(str(sys.argv[1]), cv2.CV_LOAD_IMAGE_COLOR)
        template = cv2.imread(str(sys.argv[2]), cv2.CV_LOAD_IMAGE_COLOR)
        cutoff = float(sys.argv[3])
        results = multi_match(source, template, cutoff)
        drawn = np.copy(source)
        for res in results:
            print res
            drawn = draw_bound(
                    res[0], res[1],
                    (template.shape[1], template.shape[0]),
                    drawn)
            show(drawn)
    else:
        import doctest
        doctest.testmod(verbose=True)
