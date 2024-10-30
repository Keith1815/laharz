import sys
def main():
    print("Executing LaharZ...")

    if len(sys.argv) == 1:
        from laharz import laharz
    elif sys.argv[1] == 'maintain':
        from laharz import maintain_sys_parms
    else:
        print("Unknown option. Valid option is 'maintain'. Terminating")

    print("Finished")

if __name__ == '__main__':
    sys.exit(main())