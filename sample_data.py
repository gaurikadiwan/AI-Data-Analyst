import pandas as pd
import random
from faker import Faker

fake = Faker()

regions = ["North", "South", "East", "West"]
categories = ["Electronics", "Furniture", "Accessories", "Appliances"]
products = [
    "Laptop", "Phone", "Tablet", "Chair", "Desk",
    "Monitor", "Keyboard", "Mouse", "Printer",
    "Camera"
]

data = []

# Generate only 10 rows
for i in range(1000):
    sales = random.randint(5000, 100000)
    profit = int(sales * random.uniform(0.1, 0.3))

    row = {
        "Order_ID": f"ORD{i+1:04d}",
        "Date": fake.date_between(start_date="-1y", end_date="today"),
        "Region": random.choice(regions),
        "Category": random.choice(categories),
        "Product": random.choice(products),
        "Sales": sales,
        "Profit": profit,
        "Quantity": random.randint(1, 20),
        "Customer_Rating": round(random.uniform(3.0, 5.0), 1),
        "Customer_Name": fake.name(),
        "City": fake.city()
    }

    data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Save CSV file
df.to_csv("sales_dataset_10.csv", index=False)

print("CSV created successfully: sales_dataset_10.csv")
print(df)