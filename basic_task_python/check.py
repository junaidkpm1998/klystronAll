rollNumber = [47,64,69,37,76,83, 97,10]
sampleDict ={'John':47, 'Emma':69, 'Kelly':76, 'Jason':97}
deletedNumber = []
for i in rollNumber:
    if i not in sampleDict.values():
        deletedNumber.append(i)
        rollNumber.remove(i)

print("DELETED NUMBERS : ",deletedNumber)
print("REMAINING NUMBERS : ",rollNumber)
