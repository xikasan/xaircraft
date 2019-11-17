# coding: utf-8

import numpy as np
import tensorflow as tf
from xaircraft.models.model import DefaultModel, AngleType
from xtools import simulation as xsim
tk = tf.keras


class LVAircraft(DefaultModel):
    """
    LVAircraft is an implementation of linear longitudinal(vertical) direction dynamics of the aircraft.
    For the default parameters are set to the Boeing-747.
    The linear longitudinal dynamics is written as the following:
    dx = A.x + B.u
    where, x = [u w, T, q] is a state vector, each elements representing u: speed deflection according to X-axis,
    w: speed deflection according to Z-axis, T: theta is a pitch angle, q is a pitch angle speed, positive T and q means
    pitch up; u = [Dt De] is a input vector, Dt is a thrust level deflection, De is a elevator angle deflection;
    dx is a time derivative of x, A is a state-space matrix, and B is a input matrix. A and B are described as below:
        ||        ||
    A = || ,  B = ||
        ||        ||
        ||        ||

    Radians is utilized to the angles ti represent the internal states. And inputs and outputs angles representation can
    be selected from Enum of models.AngleMode. See model.py.
    """

    def __init__(
            self,
            range_thrust=[-10, 10],
            range_elevator=[-20, 20],
            angle_type=AngleType.DEGREE,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._A, self._B = self.__construct_matrices(self.dtype)

        self.angle_type = angle_type
        range_elevator = self.import_angle(range_elevator)
        self._act_high = np.array([np.max(range_thrust), np.max(range_elevator)])
        self._act_low  = np.array([np.min(range_thrust), np.min(range_elevator)])

        self._x = self.__initiate_state()

    def __call__(self, action):
        act_t = action[0]
        act_e = action[1]
        act_e = self.import_angle(act_e)
        action = tf.concat([[act_t], [act_e]], axis=0)
        action = tf.expand_dims(action, axis=0)
        dx = self._step_body(action)
        self._x = self._x + dx * self.dt
        return self._x

    def __initiate_state(self):
        return tf.expand_dims(
            tf.Variable([0, 0, 0, 0], dtype=self.dtype), axis=0
        )

    @tf.function
    def _step_body(self, action):
        def f(x):
            return tf.matmul(x, self._A, name="Ax") + tf.matmul(action, self._B, name="Bu")
        return xsim.no_time_rungekutta(f, self.dt, self._x)

    @classmethod
    def __construct_matrices(cls, dtype):
        A = tf.constant([
            [-0.0225, 0.0022, -32.3819, 0],
            [-0.2282, -0.4038, 0, 869],
            [0, 0, 0, 1],
            [-0.0001, -0.0018, 0, -0.5518]
        ], dtype=dtype)
        B = tf.constant([
            [0.500, 0],
            [0, -0.0219],
            [0, 0],
            [0, -1.2394]
        ], dtype)
        return tf.transpose(A), tf.transpose(B)


if __name__ == '__main__':
    model = LVAircraft(dt=1/50, angle_type=AngleType.DEGREE)
    dummy_acton = tf.Variable([1, 2], dtype=model.dtype) * 1
    for _ in range(100):
        next_state = model(dummy_acton)
        print("[debug] next_state:", next_state)
