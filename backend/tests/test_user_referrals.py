from datetime import datetime

from app.models.agent import Agent, AgentCommissionMode, AgentStatus, InvitationCode, InvitationCodeStatus
from app.models.credit import CreditSource, CreditTransaction
from app.models.phone_verification import PhoneVerification
from app.models.user import MembershipType, User, UserReferralSource, UserStatus
from app.services.auth_service import AuthService
from app.services.credit_math import to_decimal


def _create_user(
    db_session,
    *,
    auth_service: AuthService,
    user_id: str,
    phone: str,
    email: str,
    nickname: str,
    credits="0",
    is_admin: bool = False,
) -> User:
    user = User(
        user_id=user_id,
        phone=phone,
        email=email,
        nickname=nickname,
        hashed_password=auth_service.get_password_hash("Password123"),
        credits=to_decimal(credits),
        membership_type=MembershipType.FREE,
        status=UserStatus.ACTIVE,
        is_admin=is_admin,
        is_phone_verified=True,
        phone_verified_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_verified_phone_record(db_session, phone: str) -> None:
    db_session.add(
        PhoneVerification(
            phone=phone,
            is_phone_verified=True,
            phone_verified_at=datetime.utcnow(),
        )
    )
    db_session.commit()


def test_register_with_user_referral_rewards_inviter(client, db_session):
    auth_service = AuthService()
    _create_user(
        db_session,
        auth_service=auth_service,
        user_id="admin_user_001",
        phone="13800000001",
        email="admin@example.com",
        nickname="管理员",
        credits="999999",
        is_admin=True,
    )
    auth_service.ensure_default_admin_invite(db_session)

    inviter = _create_user(
        db_session,
        auth_service=auth_service,
        user_id="referrer_user_001",
        phone="13800000002",
        email="referrer@example.com",
        nickname="邀请人",
        credits="5",
    )
    auth_service.ensure_user_referral_code(db_session, inviter)
    db_session.commit()
    db_session.refresh(inviter)

    _create_verified_phone_record(db_session, "13800000003")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "13800000003",
            "password": "Password123",
            "confirm_password": "Password123",
            "nickname": "新用户",
            "user_referral_code": inviter.referral_code,
        },
    )

    assert response.status_code == 200

    new_user = db_session.query(User).filter(User.phone == "13800000003").first()
    assert new_user is not None
    assert new_user.referrer_user_id == inviter.id
    assert new_user.referral_source == UserReferralSource.USER.value
    assert new_user.referral_code

    db_session.refresh(inviter)
    assert inviter.credits == to_decimal("6")

    reward_txn = (
        db_session.query(CreditTransaction)
        .filter(
            CreditTransaction.user_id == inviter.id,
            CreditTransaction.source == CreditSource.USER_REFERRAL.value,
        )
        .first()
    )
    assert reward_txn is not None
    assert reward_txn.amount == to_decimal("1")


def test_register_with_agent_invitation_rewards_agent_owner(client, db_session):
    auth_service = AuthService()
    owner = _create_user(
        db_session,
        auth_service=auth_service,
        user_id="agent_owner_001",
        phone="13800000011",
        email="agent-owner@example.com",
        nickname="代理主",
        credits="10",
    )

    agent = Agent(
        name="测试代理",
        owner_user_id=owner.id,
        status=AgentStatus.ACTIVE,
        commission_mode=AgentCommissionMode.TIERED,
    )
    db_session.add(agent)
    db_session.flush()
    db_session.add(
        InvitationCode(
            code="ABCD",
            agent_id=agent.id,
            status=InvitationCodeStatus.ACTIVE,
        )
    )
    db_session.commit()

    _create_verified_phone_record(db_session, "13800000012")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "13800000012",
            "password": "Password123",
            "confirm_password": "Password123",
            "nickname": "代理邀请用户",
            "invitation_code": "ABCD",
        },
    )

    assert response.status_code == 200

    new_user = db_session.query(User).filter(User.phone == "13800000012").first()
    assert new_user is not None
    assert new_user.agent_id == agent.id
    assert new_user.referrer_user_id == owner.id
    assert new_user.referral_source == UserReferralSource.AGENT.value

    db_session.refresh(owner)
    assert owner.credits == to_decimal("12")

    reward_txn = (
        db_session.query(CreditTransaction)
        .filter(
            CreditTransaction.user_id == owner.id,
            CreditTransaction.source == CreditSource.AGENT_INVITATION.value,
        )
        .first()
    )
    assert reward_txn is not None
    assert reward_txn.amount == to_decimal("2")


def test_user_profile_returns_referral_code_and_count(client, db_session):
    auth_service = AuthService()
    user = _create_user(
        db_session,
        auth_service=auth_service,
        user_id="profile_user_001",
        phone="13800000021",
        email="profile@example.com",
        nickname="资料用户",
        credits="8",
    )

    db_session.add_all(
        [
            User(
                user_id="child_user_001",
                phone="13800000022",
                email="child1@example.com",
                nickname="被邀请用户1",
                hashed_password=auth_service.get_password_hash("Password123"),
                credits=to_decimal("3"),
                membership_type=MembershipType.FREE,
                status=UserStatus.ACTIVE,
                referrer_user_id=user.id,
                referral_source=UserReferralSource.USER.value,
            ),
            User(
                user_id="child_user_002",
                phone="13800000023",
                email="child2@example.com",
                nickname="被邀请用户2",
                hashed_password=auth_service.get_password_hash("Password123"),
                credits=to_decimal("3"),
                membership_type=MembershipType.FREE,
                status=UserStatus.ACTIVE,
                referrer_user_id=user.id,
                referral_source=UserReferralSource.USER.value,
            ),
            User(
                user_id="child_user_003",
                phone="13800000024",
                email="child3@example.com",
                nickname="代理邀请用户",
                hashed_password=auth_service.get_password_hash("Password123"),
                credits=to_decimal("3"),
                membership_type=MembershipType.FREE,
                status=UserStatus.ACTIVE,
                referrer_user_id=user.id,
                referral_source=UserReferralSource.AGENT.value,
            ),
        ]
    )
    db_session.commit()

    tokens = auth_service.create_login_tokens(user)
    response = client.get(
        "/api/v1/user/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["referralCount"] == 2
    assert data["referralCode"]

    db_session.refresh(user)
    assert user.referral_code == data["referralCode"]
