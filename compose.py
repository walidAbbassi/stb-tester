import time

import stbt


class ResultGroupBool:
    """A container class for a list MatchResults and their group 'truthiness'

    `truthiness`: Boolean.
    `results`: List of MatchResults.
    """

    def __init__(self, truthiness, results):
        self.truthiness = truthiness
        self.results = results

    def __iter__(self):
        return self.iterate()

    def iterate(self):
        for r in self.results:
            yield r

    def __nonzero__(self):
        return self.truthiness

    def __str__(self):
        return (
            "Result Group is %s: [\n\t" % self.truthiness +
            "\n\t".join([str(res) for res in self.results]
                if self.results else ["<empty>"]) + "\n]")


def not_results(*callbacks, **opts):
    """Given a number of callbacks which returns a `ResultGroupBool`,
    this function collates these groups into a single `ResultGroupBool`,
    whose `truthiness` is not(callback1 and callback2 [and callback3 [...]])

    `**opts`:
    - `name` - Name the `not` for use in options.
    """

    def _not():
        name = (" '" + opts["name"] + "'" if "name" in opts else "")

        results = []
        boolean = True
        for cb in callbacks:
            try:
                res = cb()
                # false if any result is True
                boolean = boolean and not bool(res)
                results += res

            except (stbt.MatchAllTimeout, stbt.MotionTimeout) as e:
                stbt.debug("`not`%s: Caught exception: '%s'" % (name, e))

        ret = ResultGroupBool(boolean, results)
        stbt.debug("`not`%s: %s" % (name, ret))
        return ret

    return _not


def all_results(*callbacks, **opts):
    """Given a number of callbacks which return a `ResultGroupBool`,
    this function collates these groups into a single `ResultGroupBool`
    whose `truthiness` is True if all the sub groups are True, else False.

    `**opts`:
    - `name` - Name the `all` for use in output.
    """

    def _all():
        name = (" '" + opts["name"] + "'" if "name" in opts else "")

        results = []
        # so we can check if it was ever set
        boolean = None
        for cb in callbacks:
            try:
                res = cb()
                if boolean is None:
                    boolean = bool(res)
                else:
                    boolean = boolean and bool(res)
                results += res

            except (stbt.MatchAllTimeout, stbt.MotionTimeout) as e:
                stbt.debug("`all`%s: Caught exception: '%s'" % (name, e))

        # empty results list should be False because all callbacks
        # raised exceptions and didn't return any results.
        ret = ResultGroupBool(
                boolean if boolean is not None else False, results)
        stbt.debug("`all`%s: %s" % (name, ret))
        return ret

    return _all


def any_results(*callbacks, **opts):
    """Given a number of callbacks which return a `ResultGroupBool`,
    this function collates these groups into a single `ResultGroupBool`
    whose `truthiness` is True if any of the sub groups are True, else False.

    `**opts`:
    - `name` - Name the `any` for use in output.
    """

    def _any():
        name = (" '" + opts["name"] + "'" if "name" in opts else "")

        results = []
        boolean = False
        for cb in callbacks:
            try:
                res = cb()
                boolean = boolean or bool(res)
                results += res
            except (stbt.MatchAllTimeout, stbt.MotionTimeout) as e:
                stbt.debug("`any`%s: Caught exception: '%s'" % (name, e))

        ret = ResultGroupBool(boolean, results)
        stbt.debug("`any`%s: %s" % (name, ret))
        return ret

    return _any


_frame = None
_timestamp = None
_found_templates = []


def wait(*callbacks, **opts):
    """Wait while `*callbacks` attempt to return positve results.

    `*callbacks`: function callbacks for Wait() to call
    `**opts`:
    - `timeout_secs` - Default is 10s.
    - `name` - Name the `wait` for use in output.
    """

    def _wait():
        timeout_secs = opts["timeout_secs"] if "timeout_secs" in opts else 10
        name = (" " + opts["name"]) if "name" in opts else ""

        _callbacks = []
        for _cb in callbacks:
            _callbacks.append(_cb)

        results_over_time = {}
        global _found_templates
        _found_templates = []

        global _frame, _timestamp
        for _frame, _timestamp in stbt.frames(timeout_secs=timeout_secs):
            for cb in _callbacks:
                results = cb()

                if results:
                    _callbacks.remove(cb)

                for res in results:
                    # if we don't already have a result for the template
                    # or if the result we do have is negative
                    if (not res.template in results_over_time) or \
                            (not results_over_time[res.template]):
                        results_over_time[res.template] = res

            if not _callbacks:
                _found_templates = []
                ret = ResultGroupBool(True, results_over_time.values())
                stbt.debug("`wait`%s: exited successfully: %s" % (name, ret))
                return ret

        raise stbt.MatchAllTimeout(
            stbt.get_frame(), [t for t, r in results_over_time.items() if r],
            [t for t, r in results_over_time.items() if not r], timeout_secs)

    return _wait


def match(*templates, **opts):
    """Perform template match(es) of `templates` against current frame,
    or give `frames`, `timestamp` to the subsidiary call like:
    Match("img1.png", "img2.png")(frame, timestamp)

    `*templates`: template images to match
    `**opts`:
    - `match_parameters` - specify custom match parameters
    - `find_once` - once a template is found, do not search for it again
      (to be used when searching for multiple templates inside a `Wait()`
    """

    def _match():
        match_parameters = opts["match_parameters"] \
            if "match_parameters" in opts else stbt.MatchParameters()
        find_once = opts["find_once"] if "find_once" in opts else False

        # allow single match attempts outside of a Wait()
        global _frame, _timestamp
        if _frame is None:
            _frame, _timestamp = stbt.frames().next()

        global _found_templates
        print _found_templates

        match_results = []
        for tpl in [_ for _ in templates if _ not in _found_templates]:
            stbt.debug("Searching for '%s'" % tpl)
            matched, position, first_pass_result = stbt.match_template(
                _frame, stbt.load_image(tpl),
                match_parameters=match_parameters)

            result = stbt.MatchResult(
                timestamp=_timestamp, template=tpl, match=matched,
                position=position, first_pass_result=first_pass_result)
            stbt.debug("%s found: %s" % (
                "Match" if matched else "Weak match", str(result)))

            match_results += [result]
            if matched and find_once:
                _found_templates += [tpl]

        return ResultGroupBool(all(match_results), match_results)

    return _match


time.sleep(3)


def setup():
    for _ in range(3):
        stbt.press("ESCAPE")
        time.sleep(0.2)

    time.sleep(3)
    stbt.press("EPG")


print "\n==== TEST #1 ====\n"
setup()
wait(
    match("bbc1.png"),
    name="bbc1", timeout_secs=10)()

print "\n==== TEST #2 ====\n"
setup()
wait(
    any_results(
        match("youview.png"),
        match("minitv.png")),
    name="any")()

print "\n==== TEST #3 ====\n"
setup()
wait(
    any_results(
        match("youview.png", "bbc1.png", find_once=True),
        match("minitv.png")),
    name="double match")()
print _found_templates

print "\n==== TEST #4 ====\n"
if not_results(
        match("minitv.png"),
        name="not test")():
    print "Didn't see it."

print "\n==== TEST #5 ====\n"
setup()
wait(
    all_results(
        match("youview.png"),
        match("minitv.png")),
    name="will fail")()
