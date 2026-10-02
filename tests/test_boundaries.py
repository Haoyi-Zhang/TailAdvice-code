"""Boundary and metamorphic checks independent of the campaign selector."""
from pathlib import Path
from fractions import Fraction as Q
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from model import Job,Schedule,Segment,simulate,fcfs,max_flow
from checker import validate_trace,validate_domination,validate_prefix_reservation
from advice import make_codebook,permanent_count_moment


class BoundaryTests(unittest.TestCase):
    def test_empty(self):
        s=simulate((),Q(1,2));self.assertEqual(s,Schedule((),()))
        validate_trace((),s);self.assertEqual(max_flow((),s),0)

    def test_single_job(self):
        js=(Job(Q(7,3),Q(11,5)),)
        s=simulate(js,Q(2,3));validate_trace(js,s)
        self.assertEqual(s.completion,(Q(7,3)+Q(11,5),))

    def test_endpoints(self):
        js=(Job(Q(0),Q(2)),Job(Q(1),Q(1)),Job(Q(1),Q(1,2)))
        s=simulate(js,Q(1));validate_trace(js,s)
        self.assertEqual(s.completion,fcfs(js).completion)
        ps=simulate(js,Q(0));validate_trace(js,ps)

    def test_tied_completion_and_arrival(self):
        js=(Job(Q(0),Q(1)),Job(Q(1),Q(1)),Job(Q(1),Q(2)))
        s=simulate(js,Q(1,2));validate_trace(js,s)
        self.assertEqual(s.completion[0],1)

    def test_translation(self):
        js=(Job(Q(0),Q(3)),Job(Q(1,2),Q(2)),Job(Q(4),Q(1)))
        shift=Q(13,7)
        shifted=tuple(Job(j.release+shift,j.size) for j in js)
        a,b=simulate(js,Q(1,3)),simulate(shifted,Q(1,3))
        self.assertEqual(b.completion,tuple(c+shift for c in a.completion))

    def test_scaling(self):
        js=(Job(Q(0),Q(3)),Job(Q(1,2),Q(2)),Job(Q(4),Q(1)))
        factor=Q(7,3)
        scaled=tuple(Job(j.release*factor,j.size*factor) for j in js)
        a,b=simulate(js,Q(1,3)),simulate(scaled,Q(1,3))
        self.assertEqual(b.completion,tuple(c*factor for c in a.completion))

    def test_speed_augmentation(self):
        js=(Job(Q(0),Q(3)),Job(Q(1,4),Q(2)),Job(Q(1),Q(1)),Job(Q(2),Q(2)))
        for speed,delta in ((Q(3,2),Q(1,2)),(Q(3),Q(2))):
            a=simulate(js,delta,speed=speed)
            slow=simulate(js,Q(0),speed=speed-delta)
            validate_trace(js,a,speed);validate_domination(js,a,slow)
            validate_prefix_reservation(js,a,delta)
            self.assertLessEqual(max_flow(js,a)*delta,max_flow(js,fcfs(js)))

    def test_invalid_jobs_and_guards(self):
        for release,size in ((Q(-1),Q(1)),(Q(0),Q(0)),(Q(0),Q(-1))):
            with self.assertRaises(ValueError): Job(release,size)
        with self.assertRaises(TypeError): Job(0,Q(1))
        for g in (Q(-1),Q(2)):
            with self.assertRaises(ValueError): simulate((),g)
        with self.assertRaises(ValueError): simulate((),Q(0),speed=Q(0))
        with self.assertRaises(ValueError): simulate((),Q(0),protect='arbitrary')

    def test_zero_bit_advice_and_envelope(self):
        cb=make_codebook(0);self.assertEqual(cb.message(0),'')
        self.assertEqual(cb.select(Q(2)),0);self.assertEqual(cb.select(Q(512)),0)
        for q in (Q(1),Q(513)):
            with self.assertRaises(ValueError): cb.select(q)
        with self.assertRaises(ValueError): cb.message(1)
        with self.assertRaises(ValueError): cb.message(True)
        with self.assertRaises(ValueError): make_codebook(True)
        with self.assertRaises(ValueError): make_codebook(1,denominator=Q(1024))
        with self.assertRaises(ValueError): make_codebook(9)
        with self.assertRaises(ValueError): make_codebook(8,lower=Q(2),upper=Q(3),denominator=1)

    def test_moment_endpoints(self):
        self.assertEqual(permanent_count_moment(1,Q(0)),1)
        self.assertEqual(permanent_count_moment(1,Q(1,2)),3)
        self.assertEqual(permanent_count_moment(2,Q(1,2)),13)
        with self.assertRaises(ValueError): permanent_count_moment(1,Q(1))

    def test_malformed_traces(self):
        js=(Job(Q(0),Q(1)),)
        bad=(Schedule((Q(1),),(Segment(Q(0),Q(1),((0,Q(2)),)),)),
             Schedule((Q(1),),(Segment(Q(0),Q(1),((0,1.0),)),)),
             Schedule((Q(2),),(Segment(Q(0),Q(1),((0,Q(1)),)),)),
             Schedule((Q(1),),(Segment(Q(0),Q(1),((Q(0),Q(1)),)),)))
        for s in bad:
            with self.assertRaises(AssertionError): validate_trace(js,s)

if __name__=='__main__': unittest.main()
