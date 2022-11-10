from ipaddress import IPv4Address, IPv4Interface
from uuid import UUID

import pytest
from tests.monkey_island import InMemoryAgentRepository, InMemoryMachineRepository

from common.types import SocketAddress
from monkey_island.cc.models import Agent, Machine
from monkey_island.cc.repository import AgentMachineFacade, IAgentRepository, IMachineRepository

SEED_ID = 99
SOURCE_IP_ADDRESS = IPv4Address("10.10.10.99")

SOURCE_MACHINE_ID = 1
SOURCE_MACHINE = Machine(
    id=SOURCE_MACHINE_ID,
    hardware_id=5,
    network_interfaces=[IPv4Interface(SOURCE_IP_ADDRESS)],
)

AGENT_ID = UUID("655fd01c-5eec-4e42-b6e3-1fb738c2978d")
AGENT = Agent(
    id=AGENT_ID,
    machine_id=SOURCE_MACHINE_ID,
    start_time=0,
    parent_id=None,
    cc_server=(SocketAddress(ip="10.10.10.10", port=5000)),
)


@pytest.fixture
def agent_repository() -> IAgentRepository:
    agent_repository = InMemoryAgentRepository()
    agent_repository.upsert_agent(AGENT)

    return agent_repository


@pytest.fixture
def machine_repository() -> IMachineRepository:
    machine_repository = InMemoryMachineRepository(SEED_ID)
    machine_repository.upsert_machine(SOURCE_MACHINE)

    return machine_repository


@pytest.fixture
def agent_machine_facade(agent_repository, machine_repository) -> AgentMachineFacade:
    return AgentMachineFacade(agent_repository, machine_repository)


def test_get_machine_id_from_agent_id(agent_machine_facade):
    assert agent_machine_facade.get_machine_id_from_agent_id(AGENT_ID) == SOURCE_MACHINE_ID


def test_cache_reset__get_machine_id_from_agent_id(
    agent_machine_facade, agent_repository, machine_repository
):
    original_machine_id = agent_machine_facade.get_machine_id_from_agent_id(AGENT_ID)
    new_machine_id = original_machine_id + 100
    new_machine = Machine(
        id=new_machine_id,
        hardware_id=5,
        network_interfaces=[IPv4Interface(SOURCE_IP_ADDRESS)],
    )
    machine_repository.upsert_machine(new_machine)
    new_agent = Agent(
        id=AGENT_ID,
        machine_id=new_machine_id,
        start_time=0,
        parent_id=None,
        cc_server=(SocketAddress(ip="10.10.10.10", port=5000)),
    )

    agent_repository.reset()
    agent_repository.upsert_agent(new_agent)
    agent_machine_facade.reset_cache()
    new_machine_id = agent_machine_facade.get_machine_id_from_agent_id(AGENT_ID)

    assert original_machine_id != new_machine_id


def test_get_agent_machine(agent_machine_facade):
    assert agent_machine_facade.get_agent_machine(AGENT_ID) == SOURCE_MACHINE


def test_update_agent_machine__throws_error_if_machine_id_differs(agent_machine_facade):
    updated_machine = Machine(id=SOURCE_MACHINE.id + 100)

    with pytest.raises(ValueError):
        agent_machine_facade.update_agent_machine(AGENT_ID, updated_machine)
