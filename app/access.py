import json
from pathlib import Path
from uuid import uuid4


class JsonState:
    def __init__(self, path):
        self.path = Path(path)

    def read(self, default):
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def write(self, value):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, separators=(",", ":")))
        temporary.replace(self.path)


class AdminStore:
    def __init__(self, path, owner_id):
        self.state = JsonState(path)
        self.owner_id = owner_id

    def is_admin(self, user_id):
        return user_id == self.owner_id or user_id in self.admin_ids()

    def admin_ids(self):
        return {int(user_id) for user_id in self.state.read([])}

    def add(self, user_id):
        admin_ids = self.admin_ids()
        admin_ids.add(user_id)
        self.state.write(sorted(admin_ids))

    def remove(self, user_id):
        admin_ids = self.admin_ids()
        admin_ids.discard(user_id)
        self.state.write(sorted(admin_ids))


class PaymentStore:
    def __init__(self, path):
        self.state = JsonState(path)

    def create(self, user_id, url):
        payment_id = uuid4().hex
        payments = self.state.read({})
        payments[payment_id] = {"user_id": user_id, "url": url, "paid": False}
        self.state.write(payments)
        return payment_id

    def redeem(self, payment_id, user_id):
        payments = self.state.read({})
        payment = payments.get(payment_id)
        if not payment or payment["paid"] or payment["user_id"] != user_id:
            return None
        payment["paid"] = True
        self.state.write(payments)
        return payment["url"]
