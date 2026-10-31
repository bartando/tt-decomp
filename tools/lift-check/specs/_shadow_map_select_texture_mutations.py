"""Only behavioral FAIL counts; mutate cache copies, never checked-in source."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('ignore enable', 'map->m_config->slots[3 + layer * 2 + player].enabled == 0', 'false'),
    ('wrong enabled slot', '3 + layer * 2 + player', '3 + player * 2 + layer'),
    ('unsigned count', 'static_cast<int32_t>(map->m_draw_444) < 2', 'map->m_draw_444 < 2'),
    ('wrong count boundary', 'static_cast<int32_t>(map->m_draw_444) < 2', 'static_cast<int32_t>(map->m_draw_444) <= 2'),
    ('wrong single-player bank', 'return map->m_singlePlayerTextures[layer];', 'return map->m_activeTextures[layer];'),
    ('wrong active bank', 'return map->m_activeTextures[layer];', 'return map->m_singlePlayerTextures[layer];'),
    ('allow secondary layer', 'if (layer > 0)', 'if (layer > 1)'),
    ('wrong player', 'return map->m_playerTextures[player][layer];', 'return map->m_playerTextures[1 - player][layer];'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/pong_render.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('shadow_map_select_texture.py'),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        first = out.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {first}", flush=True)
        if not caught:
            print(out.getvalue())
            return 1
    print(f'Caught {len(CASES)}/{len(CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
