"""Reject broken prediction readback/diagnostics; only behavioral FAIL counts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
SOURCE = "src/game/ball/ball_prediction_queries.cpp"
CASES = [
    ("ball_predict_get_initial_velocities", "int BallPredict_GetInitialVelocities(", [
        ("wrong ring sample", "prediction->At(1)", "prediction->At(0)"),
        ("use singleton prediction", "prediction->m_count > 1", "prediction->m_count > 0"),
        ("omit prediction spin", "*spin = sample.angVel;", "(void)spin;"),
        ("lose homogeneous lane", "*velocity = sample.vel;", "*velocity = bpVec4{sample.vel.x, sample.vel.y, sample.vel.z, velocity->w};"),
        ("wrong active mask", "& 7", "& 1"),
        ("omit rigid body fallback", "if ((sim->level->states[handle] & 7) == 0)", "if (false)"),
        ("swap rigid velocities", "*velocity = collider->velocity;", "*velocity = collider->angularVelocity;"),
        ("wrong success result", "return 1;", "return 0;"),
    ]),
    ("ball_predict_dump", "void BallPredict_Dump(", [
        ("normalize side byte", "onLocalSide != 0", "onLocalSide == 1"),
        ("omit final bounce", "i < prediction->m_bounceCount", "i + 1 < prediction->m_bounceCount"),
        ("swap logged totals", 'local, other);', 'other, local);'),
        ("omit elapsed query", "prediction->CountBouncesSoFar(&local, &other);", "(void)prediction;"),
    ]),
]


def main():
    source=(Path(__file__).resolve().parents[3]/SOURCE).read_text()
    total=0
    for spec,signature,mutants in CASES:
        start=source.index(signature)
        end=source.index("\n}\n",start)+2
        body=source[start:end]
        for label,old,new in mutants:
            assert old in body, f"missing anchor: {spec}: {label}"
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+".py"),Options(
                    trials=256,seed=1,patches=((body,body.replace(old,new)),))).run()
            print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f"Caught {total}/{total} mutations",flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
