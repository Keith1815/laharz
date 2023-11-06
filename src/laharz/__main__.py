import sys
print("Executing LaharZ...")

if len(sys.argv) == 1:
    from laharz import laharz
elif sys.argv[1] == 'maintain':
    from laharz import maintain_sys_parms
else:
    print("Unknown option. Terminating")

print("Finished")