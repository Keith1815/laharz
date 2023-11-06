import sys
print("Executing LaharZ...")

if len(sys.argv) == 1:
    from laharz.src.laharz1 import laharz2
elif sys.argv[1] == 'maintain':
    from laharz.src.laharz1 import maintain_sys_parms
else:
    print("Unknown option. Terminating")

print("Finished")