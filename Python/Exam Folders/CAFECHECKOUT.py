print("--- Campus Café Checkout ---")
numberIced = int(input("Enter the number of Iced Lattes: "))
numberCheese = int(input("Enter the number of Cheese Empanadas: "))

total = numberIced * 85.50 + numberCheese * 35.00
print(f"\nTotal Bill: ₱ {total:.2f}")
payment = int(input(f"Enter cash payment: ₱ "))

change = payment - total
print(f"\nChange Due: ₱{change:.2f}")
print("Thank you for your purchase!")