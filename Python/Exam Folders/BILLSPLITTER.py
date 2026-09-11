print("\t===  BILL SPLITTER ===")
totalBill = float(input('Enter total bill amount: '))
people = int(input('Enter number of people: '))
tipPercent = float(input('Enter the tip: '))

tipAmount = totalBill * tipPercent / 100
grandTotal = totalBill + tipAmount
amountPerPerson = grandTotal / people

print("\n\t--- Calculation Result: ---")
print(f"Tip amount: ₱{tipAmount:.2f}")
print(f"Grand total: ₱{grandTotal:.2f}")
print(f"Each person pays: ₱{amountPerPerson:.2f}")


