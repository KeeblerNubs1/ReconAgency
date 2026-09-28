import tempfile
import unittest
from pathlib import Path

from app.access import AdminStore, PaymentStore


class AdminStoreTests(unittest.TestCase):
    def test_owner_is_always_admin_and_changes_persist(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "admins.json"
            admins = AdminStore(path, owner_id=1)

            self.assertTrue(admins.is_admin(1))
            self.assertFalse(admins.is_admin(2))
            admins.add(2)

            self.assertTrue(AdminStore(path, owner_id=1).is_admin(2))
            admins.remove(2)
            self.assertFalse(AdminStore(path, owner_id=1).is_admin(2))


class PaymentStoreTests(unittest.TestCase):
    def test_payment_can_only_be_redeemed_once_by_payer(self):
        with tempfile.TemporaryDirectory() as directory:
            payments = PaymentStore(Path(directory) / "payments.json")
            payment_id = payments.create(42, "https://zoom.us/j/123")

            self.assertIsNone(payments.redeem(payment_id, 43))
            self.assertEqual("https://zoom.us/j/123", payments.redeem(payment_id, 42))
            self.assertIsNone(payments.redeem(payment_id, 42))
