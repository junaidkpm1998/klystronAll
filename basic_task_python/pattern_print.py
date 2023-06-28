x=int(input("enter a number : "))
z=int(x/2)
y=2
for i in range(1,x+1):
    for q in range(z-1):
        print(" ", end=" ")
    for j in range(y):
        print("*", end=" ")
    print("")
    if i%2==0:
        y+=2
        z=z-1

    # print(y)