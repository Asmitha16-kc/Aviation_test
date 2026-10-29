import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

USERS = {
    "super_admin": (os.getenv("SUPERADMIN_USER_ID"), os.getenv("SUPERADMIN_PASSWORD")),
    "customer_administrator": (os.getenv("Customer_Administrator_ID"), os.getenv("Customer_Administrator_PASSWORD")),
    "finance_coordinator": (os.getenv("Finance_Coordinator_ID"), os.getenv("Finance_Coordinator_PASSWORD")),
}