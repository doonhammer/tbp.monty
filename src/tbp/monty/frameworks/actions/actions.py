# Copyright 2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from __future__ import annotations

from abc import ABC, abstractmethod
from json import JSONDecoder, JSONEncoder
from typing import TYPE_CHECKING, Tuple

from numpy import ndarray

if TYPE_CHECKING:
    from tbp.monty.frameworks.actions.action_samplers import ActionSampler
    from tbp.monty.frameworks.actions.actuator import Actuator

__all__ = [
    # Actions
    "Action",
    "LookDown",
    "LookUp",
    "MoveForward",
    "MoveTangentially",
    "OrientHorizontal",
    "OrientVertical",
    "SetAgentPitch",
    "SetAgentPose",
    "SetSensorPitch",
    "SetSensorPose",
    "SetSensorRotation",
    "SetYaw",
    "TurnLeft",
    "TurnRight",
    # Spatial representations
    "QuaternionWXYZ",
    "VectorXYZ",
]

VectorXYZ = Tuple[float, float, float]
QuaternionWXYZ = Tuple[float, float, float, float]


class Action(ABC):
    """An action that can be taken by an agent.

    Actions are generated by the MotorSystem and are executed by an Actuator.
    """

    @staticmethod
    def _camel_case_to_snake_case(name: str) -> str:
        """Expecting a class name in CamelCase returns it in snake_case.

        Returns:
            The class name in snake_case.
        """
        return "".join(
            ["_" + char.lower() if char.isupper() else char for char in name]
        ).lstrip("_")

    @classmethod
    def action_name(cls) -> str:
        """Generate action name based on class.

        Used in static configuration, e.g., `FakeAction.action_name()`.

        Returns:
            The action name in snake_case.
        """
        return Action._camel_case_to_snake_case(cls.__name__)

    @classmethod
    @abstractmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> Action:
        """Uses the sampler to sample an instance of this action."""
        pass

    @property
    def name(self) -> str:
        """Used for checking action name on an Action instance."""
        return self.__class__.action_name()

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id

    def __iter__(self):
        """Yields the action name and all action parameters.

        Useful if you want to do something like: `dict(action_instance)`.
        """
        yield "action", self.name
        for key, value in self.__dict__.items():
            if key == "name":
                continue
            yield key, value

    @abstractmethod
    def act(self, actuator: Actuator) -> None:
        """Execute the action using the provided actuator."""
        pass


class LookDown(Action):
    """Rotate the agent downwards by a specified number of degrees."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> LookDown:
        return sampler.sample_look_down(agent_id)

    def __init__(
        self, agent_id: str, rotation_degrees: float, constraint_degrees: float = 90.0
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.constraint_degrees = constraint_degrees
        self.rotation_degrees = rotation_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_look_down(self)


class LookUp(Action):
    """Rotate the agent upwards by a specified number of degrees."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> LookUp:
        return sampler.sample_look_up(agent_id)

    def __init__(
        self, agent_id: str, rotation_degrees: float, constraint_degrees: float = 90.0
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.constraint_degrees = constraint_degrees
        self.rotation_degrees = rotation_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_look_up(self)


class MoveForward(Action):
    """Move the agent forward by a specified distance."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> MoveForward:
        return sampler.sample_move_forward(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_move_forward(self)


class MoveTangentially(Action):
    """Move the agent tangentially.

    Moves the agent tangentially to the current orientation by a specified distance
    along a specified direction.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> MoveTangentially:
        return sampler.sample_move_tangentially(agent_id)

    def __init__(self, agent_id: str, distance: float, direction: VectorXYZ) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance
        self.direction = direction

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_move_tangentially(self)


class OrientHorizontal(Action):
    """Move the agent in the horizontal plane.

    Moves the agent in the horizontal plane compensating for the horizontal
    motion with a rotation in the horizontal plane.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> OrientHorizontal:
        return sampler.sample_orient_horizontal(agent_id)

    def __init__(
        self,
        agent_id: str,
        rotation_degrees: float,
        left_distance: float,
        forward_distance: float,
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_degrees = rotation_degrees
        self.left_distance = left_distance
        self.forward_distance = forward_distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_orient_horizontal(self)


class OrientVertical(Action):
    """Move the agent in the vertical plane.

    Moves the agent in the vertical plane compensating for the vertical motion
    with a rotation in the vertical plane.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> OrientVertical:
        return sampler.sample_orient_vertical(agent_id)

    def __init__(
        self,
        agent_id: str,
        rotation_degrees: float,
        down_distance: float,
        forward_distance: float,
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_degrees = rotation_degrees
        self.down_distance = down_distance
        self.forward_distance = forward_distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_orient_vertical(self)


class SetAgentPitch(Action):
    """Set the agent pitch rotation in degrees.

    Note that unless otherwise changed, the sensors maintain identity orientation
    with regard to the agent. So, this will also adjust the pitch of agent's sensors
    with regard to the environment.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetAgentPitch:
        return sampler.sample_set_agent_pitch(agent_id)

    def __init__(self, agent_id: str, pitch_degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.pitch_degrees = pitch_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_agent_pitch(self)


class SetAgentPose(Action):
    """Set the agent pose.

    Set the agent pose to absolute location coordinates and orientation in the
    environment.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetAgentPose:
        return sampler.sample_set_agent_pose(agent_id)

    def __init__(
        self, agent_id: str, location: VectorXYZ, rotation_quat: QuaternionWXYZ
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.location = location
        self.rotation_quat = rotation_quat

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_agent_pose(self)


class SetSensorPitch(Action):
    """Set the sensor pitch rotation.

    Note that this does not update the pitch of the agent. Imagine the body associated
    with the eye remaining in place, while the eye moves.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetSensorPitch:
        return sampler.sample_set_sensor_pitch(agent_id)

    def __init__(self, agent_id: str, pitch_degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.pitch_degrees = pitch_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_sensor_pitch(self)


class SetSensorPose(Action):
    """Set the sensor pose.

    Set the sensor pose to absolute location coordinates and orientation in the
    environment.
    """

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetSensorPose:
        return sampler.sample_set_sensor_pose(agent_id)

    def __init__(
        self, agent_id: str, location: VectorXYZ, rotation_quat: QuaternionWXYZ
    ) -> None:
        super().__init__(agent_id=agent_id)
        self.location = location
        self.rotation_quat = rotation_quat

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_sensor_pose(self)


class SetSensorRotation(Action):
    """Set the sensor rotation relative to the agent."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetSensorRotation:
        return sampler.sample_set_sensor_rotation(agent_id)

    def __init__(self, agent_id: str, rotation_quat: QuaternionWXYZ) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_quat = rotation_quat

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_sensor_rotation(self)


class SetYaw(Action):
    """Set the agent body yaw rotation."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> SetYaw:
        return sampler.sample_set_yaw(agent_id)

    def __init__(self, agent_id: str, rotation_degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_degrees = rotation_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_set_yaw(self)


class TurnLeft(Action):
    """Rotate the agent to the left."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> TurnLeft:
        return sampler.sample_turn_left(agent_id)

    def __init__(self, agent_id: str, rotation_degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_degrees = rotation_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_turn_left(self)


class TurnRight(Action):
    """Rotate the agent to the right."""

    @classmethod
    def sample(cls, agent_id: str, sampler: ActionSampler) -> TurnRight:
        return sampler.sample_turn_right(agent_id)

    def __init__(self, agent_id: str, rotation_degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.rotation_degrees = rotation_degrees

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_turn_right(self)


class ActionJSONEncoder(JSONEncoder):
    """Encodes an Action into a JSON object.

    Action name is encoded as the `"action"` parameter. All other Action
    parameters are encoded as key-value pairs in the JSON object
    """

    def default(self, obj):
        if isinstance(obj, Action):
            o = {}
            for key, value in dict(obj).items():
                if isinstance(value, ndarray):
                    o[key] = value.tolist()
                else:
                    o[key] = value
            return o
        return super().default(obj)


class ActionJSONDecoder(JSONDecoder):
    """Decodes JSON object into Actions.

    Requires that the JSON object contains an "action" key with the name of the action.
    Additionally, the JSON object must contain all action parameters used by the action.
    """

    def __init__(self):
        super().__init__(object_hook=self.object_hook)

    def object_hook(self, obj):
        if "action" not in obj:
            raise ValueError("Invalid action object: missing 'action' key.")
        action = obj["action"]
        if action == LookDown.action_name():
            return LookDown(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
                constraint_degrees=obj["constraint_degrees"],
            )
        elif action == LookUp.action_name():
            return LookUp(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
                constraint_degrees=obj["constraint_degrees"],
            )
        elif action == MoveForward.action_name():
            return MoveForward(
                agent_id=obj["agent_id"],
                distance=obj["distance"],
            )
        elif action == MoveTangentially.action_name():
            return MoveTangentially(
                agent_id=obj["agent_id"],
                distance=obj["distance"],
                direction=tuple(obj["direction"]),
            )
        elif action == OrientHorizontal.action_name():
            return OrientHorizontal(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
                left_distance=obj["left_distance"],
                forward_distance=obj["forward_distance"],
            )
        elif action == OrientVertical.action_name():
            return OrientVertical(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
                down_distance=obj["down_distance"],
                forward_distance=obj["forward_distance"],
            )
        elif action == SetAgentPitch.action_name():
            return SetAgentPitch(
                agent_id=obj["agent_id"],
                pitch_degrees=obj["pitch_degrees"],
            )
        elif action == SetAgentPose.action_name():
            return SetAgentPose(
                agent_id=obj["agent_id"],
                location=tuple(obj["location"]),
                rotation_quat=tuple(obj["rotation_quat"]),
            )
        elif action == SetSensorPitch.action_name():
            return SetSensorPitch(
                agent_id=obj["agent_id"],
                pitch_degrees=obj["pitch_degrees"],
            )
        elif action == SetSensorPose.action_name():
            return SetSensorPose(
                agent_id=obj["agent_id"],
                location=tuple(obj["location"]),
                rotation_quat=tuple(obj["rotation_quat"]),
            )
        elif action == SetSensorRotation.action_name():
            return SetSensorRotation(
                agent_id=obj["agent_id"],
                rotation_quat=tuple(obj["rotation_quat"]),
            )
        elif action == SetYaw.action_name():
            return SetYaw(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
            )
        elif action == TurnLeft.action_name():
            return TurnLeft(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
            )
        elif action == TurnRight.action_name():
            return TurnRight(
                agent_id=obj["agent_id"],
                rotation_degrees=obj["rotation_degrees"],
            )
        else:
            raise ValueError(f"Invalid action object: unknown action '{action}'.")
