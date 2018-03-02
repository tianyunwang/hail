from hail.genetics.reference_genome import ReferenceGenome, reference_genome_type
from hail.genetics.locus import Locus
from hail.typecheck import *
from hail.utils.java import *
import hail as hl

interval_type = lazy()

class Interval(object):
    """
    A genomic interval marked by start and end loci.

    >>> interval1 = hl.Interval.parse('X:100005-X:150020')
    >>> interval2 = hl.Interval.parse('16:29500000-30200000')

    :param start: inclusive start locus
    :type start: :class:`.Locus`
    :param end: exclusive end locus
    :type end: :class:`.Locus`
    """

    @typecheck_method(start=Locus,
                      end=Locus)
    def __init__(self, start, end):
        if start._rg != end._rg:
            raise TypeError(
                "expect `start' and `end' to have the same reference genome but found ({}, {})".format(start._rg.name,
                                                                                                       end._rg.name))
        self._rg = start._rg
        self._jrep = scala_object(Env.hail().variant, 'Locus').makeInterval(start._jrep, end._jrep, self._rg._jrep)

        # FIXME
        from hail.expr.types import tlocus
        self._typ = tlocus(self._rg)

    def __str__(self):
        return self._jrep.toString()

    def __repr__(self):
        return 'Interval(start=%s, end=%s)' % (repr(self.start), repr(self.end))

    def __eq__(self, other):
        return isinstance(other, Interval) and self._jrep.equals(other._jrep) and self._rg._jrep == other._rg._jrep

    def __hash__(self):
        return self._jrep.hashCode()

    @classmethod
    def _from_java(cls, jrep, reference_genome):
        interval = Interval.__new__(cls)
        interval._jrep = jrep
        interval._rg = reference_genome

        # FIXME
        from hail.expr.types import tlocus
        interval._typ = tlocus(reference_genome)

        reference_genome._check_interval(jrep)

        super(Interval, interval).__init__()
        return interval

    @classmethod
    @typecheck_method(string=str,
                      reference_genome=reference_genome_type)
    def parse(cls, string, reference_genome='default'):
        """Parses a genomic interval from string representation.

        **Examples**:

        >>> interval_1 = hl.Interval.parse('X:100005-X:150020')
        >>> interval_2 = hl.Interval.parse('16:29500000-30200000')
        >>> interval_3 = hl.Interval.parse('16:29.5M-30.2M')  # same as interval_2
        >>> interval_4 = hl.Interval.parse('16:30000000-END')
        >>> interval_5 = hl.Interval.parse('16:30M-END')  # same as interval_4
        >>> interval_6 = hl.Interval.parse('1-22')  # autosomes
        >>> interval_7 = hl.Interval.parse('X')  # all of chromosome X


        There are several acceptable representations.

        ``CHR1:POS1-CHR2:POS2`` is the fully specified representation, and
        we use this to define the various shortcut representations.

        In a ``POS`` field, ``start`` (``Start``, ``START``) stands for 0.

        In a ``POS`` field, ``end`` (``End``, ``END``) stands for max int.

        In a ``POS`` field, the qualifiers ``m`` (``M``) and ``k`` (``K``) multiply
        the given number by ``1,000,000`` and ``1,000``, respectively.  ``1.6K`` is short for
        1600, and ``29M`` is short for 29000000.

        ``CHR:POS1-POS2`` stands for ``CHR:POS1-CHR:POS2``

        ``CHR1-CHR2`` stands for ``CHR1:START-CHR2:END``

        ``CHR`` stands for ``CHR:START-CHR:END``

        Note that the start locus must precede the start locus.

        Parameters
        ----------
        string : :obj:`str`
            String to parse.
        reference_genome : :obj:`str` or :class:`.ReferenceGenome`
            Reference genome to use.

        Returns
        -------
        :class:`.Interval`
        """

        jrep = scala_object(Env.hail().variant, 'Locus').parseInterval(string, reference_genome._jrep)
        return Interval._from_java(jrep, reference_genome)

    @property
    def start(self):
        """
        Locus object referring to the start of the interval (inclusive).

        :rtype: :class:`.Locus`
        """
        return Locus._from_java(self._jrep.start(), self._rg)

    @property
    def end(self):
        """
        Locus object referring to the end of the interval (exclusive).

        :rtype: :class:`.Locus`
        """
        return Locus._from_java(self._jrep.end(), self._rg)

    @property
    def reference_genome(self):
        """Reference genome.

        :return: :class:`.ReferenceGenome`
        """
        return self._rg

    @typecheck_method(locus=Locus)
    def contains(self, locus):
        """True if the supplied locus is contained within the interval.

        This membership check is left-inclusive, right-exclusive.  This
        means that the interval 1:100-101 includes 1:100 but not 1:101.

        :type: locus: :class:`.Locus.`
        :rtype: bool
        """

        if self._rg != locus._rg:
            raise TypeError(
                "expect `locus' has reference genome `{}' but found `{}'".format(self._rg.name, locus._rg.name))
        return self._jrep.contains(self._typ._jtype.ordering(), locus._jrep)

    @typecheck_method(interval=interval_type)
    def overlaps(self, interval):
        """True if the the supplied interval contains any locus in common with this one.

        The statement

        >>> interval1.overlaps(interval2)

        is equivalent to

        >>> interval1.contains(interval2.start) or interval2.contains(interval1.start)

        :type: interval: :class:`.Interval`
        :rtype: bool"""

        if self._rg != interval._rg:
            raise TypeError(
                "expect `interval' has reference genome `{}' but found `{}'".format(self._rg.name, interval._rg.name))
        return self._jrep.mayOverlap(self._typ._jtype.ordering(), interval._jrep)

interval_type.set(Interval)
