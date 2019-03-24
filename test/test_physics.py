import os
import logging
_logger = logging.getLogger(__name__)
import numpy as np


from utils import gen_filename, git_head_hash
from poolvr.physics.events import PhysicsEvent, CueStrikeEvent, BallSlidingEvent, BallRollingEvent, BallRestEvent#, BallCollisionEvent



INCH2METER = 0.0254
ball_radius = 1.125 * INCH2METER
ball_diameter = 2*ball_radius
ball_mass = 0.17
ball_I = 2.0/5 * ball_mass * ball_radius**2
mu_r = 0.016 # coefficient of rolling friction between ball and table
mu_sp = 0.044 # coefficient of spinning friction between ball and table
mu_s = 0.2 # coefficient of sliding friction between ball and table
mu_b = 0.06 # coefficient of friction between ball and cushions
g = 9.81 # magnitude of acceleration due to gravity
c_b = 4000.0 # ball material's speed of sound
E_Y_b = 2.4e9 # ball material's Young's modulus of elasticity
_ZERO_TOLERANCE = 1e-8
_ZERO_TOLERANCE_SQRD = _ZERO_TOLERANCE**2
PIx2 = 2*np.pi


_here = os.path.dirname(__file__)


def test_occlusion(physics, request):
    assert (physics._occ_ij == ~np.array([[0,1,1,1,1,1,1,0,0,0,1,0,0,1,0,1],
                                          [1,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0],
                                          [1,1,0,1,0,0,1,1,0,0,0,0,0,0,0,0],
                                          [1,0,1,0,1,0,0,1,1,0,0,0,0,0,0,0],
                                          [1,0,0,1,0,1,0,0,1,1,0,0,0,0,0,0],
                                          [1,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0],
                                          [1,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0],
                                          [0,0,1,1,0,0,1,0,1,0,1,1,0,0,0,0],
                                          [0,0,0,1,1,0,0,1,0,1,0,1,1,0,0,0],
                                          [0,0,0,0,1,1,0,0,1,0,0,0,1,0,0,0],
                                          [1,0,0,0,0,0,1,1,0,0,0,1,0,1,0,0],
                                          [0,0,0,0,0,0,0,1,1,0,1,0,1,1,1,0],
                                          [0,0,0,0,0,0,0,0,1,1,0,1,0,0,1,0],
                                          [1,0,0,0,0,0,0,0,0,0,1,1,0,0,1,1],
                                          [0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,1],
                                          [1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0]], dtype=np.bool)).all()
    show_plots, save_plots = request.config.getoption('show_plots'), request.config.getoption('save_plots')
    if not (show_plots or save_plots):
        return
    import matplotlib.pyplot as plt
    plt.imshow(physics._occ_ij)
    if show_plots:
        plt.show()
    if save_plots:
        try:
            filename = os.path.join(os.path.dirname(__file__), 'plots', 'test_occlusion.png')
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                    os.makedirs(dirname, exist_ok=True)
            plt.savefig(filename)
            _logger.info('saved plot to "%s"', filename)
        except Exception as err:
            _logger.error(err)
    plt.close()


def test_strike_ball(physics,
                     plot_motion_z_position,
                     plot_motion_timelapse,
                     plot_energy):
    physics.reset(balls_on_table=[0])
    ball_positions = physics.eval_positions(0.0)
    r_c = ball_positions[0].copy()
    r_c[2] += ball_radius
    V = np.zeros(3, dtype=np.float64)
    V[2] = -0.6
    M = 0.54
    events = physics.strike_ball(0.0, 0, ball_positions[0], r_c, V, M)
    _logger.debug('strike on %d resulted in %d events:\n\n%s\n', 0, len(events),
                  PhysicsEvent.events_str(events))
    assert 4 == len(events)
    assert isinstance(events[0], CueStrikeEvent)
    assert isinstance(events[1], BallSlidingEvent)
    assert isinstance(events[2], BallRollingEvent)
    assert isinstance(events[3], BallRestEvent)


def test_ball_collision(physics,
                        plot_motion_z_position,
                        plot_motion_timelapse,
                        plot_energy,
                        gl_rendering):
    ball_positions = physics.eval_positions(0.0)
    ball_positions[1] = ball_positions[0]; ball_positions[1,2] -= 8 * ball_radius
    physics.reset(balls_on_table=[0, 1],
                  ball_positions=ball_positions)
    start_event = BallSlidingEvent(0, 0, r_0=ball_positions[0],
                                   v_0=np.array((0.0, 0.0, -0.6)),
                                   omega_0=np.zeros(3, dtype=np.float64))
    events = physics.add_event_sequence(start_event)
    _logger.debug('%d events added:\n\n%s\n', len(events), PhysicsEvent.events_str(events=events))
    # assert 6 == len(events)
    # assert isinstance(events[0], BallSlidingEvent)
    # assert isinstance(events[1], BallRollingEvent)
    # assert isinstance(events[2], BallCollisionEvent)
    # assert isinstance(events[3], BallRestEvent)
    # assert isinstance(events[4], BallRollingEvent)
    # assert isinstance(events[5], BallRestEvent)


def test_angled_ball_collision(physics,
                               plot_motion_z_position,
                               plot_motion_x_position,
                               plot_motion_timelapse,
                               plot_energy,
                               gl_rendering):
    ball_positions = physics.eval_positions(0.0)
    ball_positions[1] = ball_positions[0]
    ball_positions[1,0] -= 8 / np.sqrt(2) * ball_radius
    ball_positions[1,2] -= 8 / np.sqrt(2) * ball_radius
    physics.reset(balls_on_table=[0, 1],
                  ball_positions=ball_positions)
    r_ij = ball_positions[1] - ball_positions[0]
    r_ij[0] += ball_radius
    e_ij = r_ij / np.linalg.norm(r_ij)
    v_0 = 0.9 * e_ij
    start_event = BallSlidingEvent(0, 0, r_0=ball_positions[0],
                                   v_0=v_0,
                                   omega_0=np.zeros(3, dtype=np.float64))
    events = physics.add_event_sequence(start_event)
    _logger.debug('%d events added:\n\n%s\n', len(events), PhysicsEvent.events_str(events=events))
    # assert 6 == len(events)
    # assert isinstance(events[0], BallSlidingEvent)
    # assert isinstance(events[1], BallRollingEvent)
    # assert isinstance(events[2], BallCollisionEvent)
    # assert isinstance(events[3], BallRestEvent)
    # assert isinstance(events[4], BallRollingEvent)
    # assert isinstance(events[5], BallRestEvent)


def test_sliding_ball_collision(physics,
                                plot_motion_z_position,
                                plot_motion_timelapse,
                                plot_energy,
                                gl_rendering):
    ball_positions = physics.eval_positions(0.0)
    ball_positions[1] = ball_positions[0]; ball_positions[1,2] -= 8 * ball_radius
    physics.reset(balls_on_table=[0, 1],
                  ball_positions=ball_positions)
    start_event = BallSlidingEvent(0, 0, r_0=ball_positions[0],
                                   v_0=np.array((0.0, 0.0, -2.0)),
                                   omega_0=np.zeros(3, dtype=np.float64))
    events = physics.add_event_sequence(start_event)
    _logger.debug('%d events added:\n\n%s\n', len(events), PhysicsEvent.events_str(events=events))
    # assert 6 == len(events)
    # assert isinstance(events[0], BallSlidingEvent)
    # assert isinstance(events[1], BallCollisionEvent)
    # assert isinstance(events[2], BallRestEvent)
    # assert isinstance(events[3], BallSlidingEvent)
    # assert isinstance(events[4], BallRollingEvent)
    # assert isinstance(events[5], BallRestEvent)


def test_break(pool_physics,
               plot_motion_timelapse,
               plot_energy,
               gl_rendering):
    physics = pool_physics
    ball_positions = physics.eval_positions(0.0)
    r_c = ball_positions[0].copy()
    r_c[2] += ball_radius
    V = np.array((-0.01, 0.0, -1.6), dtype=np.float64)
    #V = np.array((-0.01, 0.0, -2.5), dtype=np.float64)
    M = 0.54
    outname = gen_filename('test_break.%s' % git_head_hash(), 'pstats', directory=_here)
    from time import perf_counter
    import cProfile
    pr = cProfile.Profile()
    pr.enable()
    t0 = perf_counter()
    events = physics.strike_ball(0.0, 0, ball_positions[0], r_c, V, M)
    t1 = perf_counter()
    pr.dump_stats(outname)
    _logger.info('...dumped stats to "%s"', outname)
    _logger.info('elapsed time: %s', t1-t0)
    _logger.debug('strike on %d resulted in %d events:\n\n%s\n', 0, len(events),
                  PhysicsEvent.events_str(events))


def test_break_and_following_shot(pool_physics,
                                  gl_rendering):
    physics = pool_physics
    ball_positions = physics.eval_positions(0.0)
    r_c = ball_positions[0].copy()
    r_c[2] += ball_radius
    V = np.array((-0.01, 0, -1.6), dtype=np.float64)
    M = 0.54
    events = physics.strike_ball(0.0, 0, ball_positions[0], r_c, V, M)
    _logger.debug('strike #1 on %d resulted in %d events:\n\n%s\n',
                  0, len(events), PhysicsEvent.events_str(events))
    ntt = physics.next_turn_time
    ball_positions = physics.eval_positions(ntt)
    r_02 = ball_positions[2] - ball_positions[0]
    r_02_mag = np.sqrt(np.dot(r_02, r_02))
    n_02 = r_02 / r_02_mag
    r_c = ball_positions[0] - ball_radius * n_02
    V = 0.99 * n_02
    events = physics.strike_ball(ntt, 0, ball_positions[0], r_c, V, M)
    _logger.debug('strike #2 on %d resulted in %d events:\n\n%s\n',
                  0, len(events), PhysicsEvent.events_str(events))


def test_strike_ball_english(pool_physics,
                             gl_rendering,
                             plot_motion_timelapse):
    physics = pool_physics
    ball_positions = physics.eval_positions(0.0)
    r_c = ball_positions[0].copy()
    sy = np.sin(45*np.pi/180)
    cy = np.cos(45*np.pi/180)
    sxz = np.sin(80*np.pi/180)
    cxz = np.cos(80*np.pi/180)
    r_c[1] += ball_radius * sy
    r_c[0] += ball_radius * cy * sxz
    r_c[2] += ball_radius * cy * cxz
    V = np.zeros(3, dtype=np.float64)
    V[2] = -1.5
    M = 0.54
    events = physics.strike_ball(0.0, 0, ball_positions[0], r_c, V, M)
    _logger.debug('strike on %d resulted in %d events:\n\n%s\n', 0, len(events),
                  PhysicsEvent.events_str(events))


def test_strike_ball_less_english(pool_physics,
                                  gl_rendering,
                                  plot_motion_timelapse):
    physics = pool_physics
    ball_positions = physics.eval_positions(0.0)
    r_c = ball_positions[0].copy()
    sy = np.sin(40*np.pi/180)
    cy = np.cos(40*np.pi/180)
    sxz = np.sin(30*np.pi/180)
    cxz = np.cos(30*np.pi/180)
    r_c[1] += ball_radius * sy
    r_c[0] += ball_radius * cy * sxz
    r_c[2] += ball_radius * cy * cxz
    V = np.zeros(3, dtype=np.float64)
    V[2] = -1.5
    M = 0.54
    events = physics.strike_ball(0.0, 0, ball_positions[0], r_c, V, M)
    _logger.debug('strike on %d resulted in %d events:\n\n%s\n', 0, len(events),
                  PhysicsEvent.events_str(events))


# def test_pocket_scratch(pool_physics,
#                         gl_rendering,
#                         plot_motion_timelapse,
#                         plot_energy):
#     physics = pool_physics
#     ball_positions = physics.eval_positions(0.0)
#     physics.reset(balls_on_table=[0],
#                   ball_positions=ball_positions)
#     r_p = np.array(physics.table.pocket_positions[0])
#     r_0p = r_p - ball_positions[0]
#     v_0 = 1.9 * r_0p / np.sqrt(np.dot(r_0p, r_0p))
#     start_event = BallSlidingEvent(0, 0, r_0=ball_positions[0],
#                                    v_0=v_0,
#                                    omega_0=np.zeros(3, dtype=np.float64))
#     events = physics.add_event_sequence(start_event)
#     _logger.debug('%d events added:\n\n%s\n', len(events), PhysicsEvent.events_str(events=events))


def test_quartic_solve(pool_physics):
    physics = pool_physics
    def quadratic_solve(p):
        a, b, c = p[::-1]
        d = b**2 - 4*a*c
        if d < 0:
            sqrtd = np.sqrt(d + 0j)
        else:
            sqrtd = np.sqrt(d)
        return [(-b + sqrtd) / (2*a), (-b - sqrtd) / (2*a)]
    p = np.array([9, 0, 0, 0, 1], dtype=np.float64)
    xs = physics.quartic_solve(p)
    q0 = np.array([3, np.sqrt(6), 1], dtype=np.float64)
    q1 = q0.copy(); q1[1] *= -1
    _logger.debug('''roots of x^4 + 9
which factors into quadratics
  (x^2 + 6^0.5*x + 3): %s
  (x^2 - 6^0.5*x + 3): %s

%s
''',
                  ',  '.join(str(x) for x in quadratic_solve(q0)),
                  ',  '.join(str(x) for x in quadratic_solve(q1)),
                  ',  '.join(str(x) for x in xs))
    p = np.array([-3, -2, -1, 2, 1], dtype=np.float64)
    xs = physics.quartic_solve(p)
    q0 = np.array([1, 1, 1], dtype=np.float64)
    q1 = np.array([-3, 1, 1], dtype=np.float64)
    _logger.debug('''roots of x^4 + 2x^3 - x^2 - 2x - 3
which factors into quadratics
  (x^2 + x + 1): %s
  (x^2 + x - 3): %s

%s
''',
                  ',  '.join(str(x) for x in quadratic_solve(q0)),
                  ',  '.join(str(x) for x in quadratic_solve(q1)),
                  ',  '.join(str(x) for x in xs))
    np.random.seed(1)
    for _ in range(1):
        a, b, c, d = xs = np.random.rand(4)
        p = np.array([
            1,
            (-a - b - c - d),
            (a*b + a*c + a*d + b*c + b*d + c*d),
            (-a*b*c - a*b*d - a*c*d - b*c*d),
            a*b*c*d
        ][::-1])
        zs = physics.quartic_solve(p)
        _logger.debug('''roots of x^4 + (%s)x^3 + (%s)x^2 + (%s)x + %s
which factors into
(x - %s)
(x - %s)
(x - %s)
(x - %s)

%s
''',
                      p[3], p[2], p[1], p[0], a, b, c, d,
                      ',  '.join(str(x) for x in zs))
        for z in zs:
            e = abs(xs - z)/abs(xs)
            assert((e < 1e-8).any())
