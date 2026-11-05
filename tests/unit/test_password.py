from pet_orders.core.auth.password import (
    SECRET_LENGTH,
    generate_auth_code,
    hash_auth_code,
    hash_password,
    verify_auth_code,
    verify_password,
)


async def test_verify_password():
    hashed = await hash_password('password')

    assert hashed != 'password'
    assert await verify_password('password', hashed) is True
    assert await verify_password('wrong-password', hashed) is False


def test_generate_auth_code():
    code = generate_auth_code()

    assert len(code) == SECRET_LENGTH
    assert code.isdigit()


def test_verify_auth_code():
    hashed = hash_auth_code('123456')

    assert verify_auth_code('123456', hashed) is True
    assert verify_auth_code('654321', hashed) is False
    assert verify_auth_code('123456', '') is False
