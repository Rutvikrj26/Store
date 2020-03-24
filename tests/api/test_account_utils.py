from saleor.core.permissions import AccountPermissions, OrderPermissions
from saleor.graphql.account.utils import (
    can_user_manage_group,
    get_group_permission_codes,
    get_out_of_scope_permissions,
    get_user_permissions,
)


def test_can_manage_group_user_without_permissions(
    staff_user, permission_group_manage_users
):
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is False


def test_can_manage_group_user_with_different_permissions(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is False


def test_can_manage_group(
    staff_user,
    permission_group_manage_users,
    permission_manage_users,
    permission_manage_orders,
):
    staff_user.user_permissions.add(permission_manage_users, permission_manage_orders)
    result = can_user_manage_group(staff_user, permission_group_manage_users)
    assert result is True


def test_can_manage_group_user_superuser(
    admin_user, permission_group_manage_users, permission_manage_orders
):
    result = can_user_manage_group(admin_user, permission_group_manage_users)
    assert result is True


def test_get_out_of_scope_permissions_user_has_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders, permission_manage_users)
    result = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert result == []


def test_get_out_of_scope_permissions_user_does_not_have_all_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    staff_user.user_permissions.add(permission_manage_orders)
    result = get_out_of_scope_permissions(
        staff_user, [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    )
    assert result == [AccountPermissions.MANAGE_USERS]


def test_get_out_of_scope_permissions_user_without_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    permissions = [AccountPermissions.MANAGE_USERS, OrderPermissions.MANAGE_ORDERS]
    result = get_out_of_scope_permissions(staff_user, permissions)
    assert result == permissions


def test_get_group_permission_codes(
    permission_group_manage_users, permission_manage_orders
):
    group = permission_group_manage_users
    permission_codes = get_group_permission_codes(group)

    expected_result = {
        f"{perm.content_type.app_label}.{perm.codename}"
        for perm in group.permissions.all()
    }
    assert len(permission_codes) == group.permissions.count()
    assert set(permission_codes) == expected_result


def test_get_group_permission_codes_group_without_permissions(
    permission_group_manage_users, permission_manage_orders
):
    group = permission_group_manage_users
    group.permissions.clear()
    permission_codes = get_group_permission_codes(group)

    assert len(permission_codes) == group.permissions.count()
    assert set(permission_codes) == set()


def test_get_user_permissions(permission_group_manage_users, permission_manage_orders):
    staff_user = permission_group_manage_users.user_set.first()
    group_permissions = permission_group_manage_users.permissions.all()
    staff_user.user_permissions.add(permission_manage_orders)

    permissions = get_user_permissions(staff_user)

    expected_permissions = group_permissions | staff_user.user_permissions.all()
    assert set(permissions.values_list("codename", flat=True)) == set(
        expected_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_only_group_permissions(permission_group_manage_users):
    staff_user = permission_group_manage_users.user_set.first()
    group_permissions = permission_group_manage_users.permissions.all()

    permissions = get_user_permissions(staff_user)

    assert set(permissions.values_list("codename", flat=True)) == set(
        group_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_only_permissions(staff_user, permission_manage_orders):
    staff_user.user_permissions.add(permission_manage_orders)

    permissions = get_user_permissions(staff_user)

    expected_permissions = staff_user.user_permissions.all()
    assert set(permissions.values_list("codename", flat=True)) == set(
        expected_permissions.values_list("codename", flat=True)
    )


def test_get_user_permissions_no_permissions(staff_user):
    permissions = get_user_permissions(staff_user)

    assert not permissions