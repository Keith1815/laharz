import sys
print("Executing LaharZ")
print("Let's read the arguments from command line")
print(sys.argv[1])
if len(sys.argv) == 1:
    from laharz.src import laharz
elif sys.argv[1] == 'maintain':
    from laharz.src import maintain_sys_parms
else:
    print("Unknown option. Terminating")

