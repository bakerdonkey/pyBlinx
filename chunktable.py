import extract
import argparse

def main() :
    parser = argparse.ArgumentParser()
    parser.add_argument('datapath', help='Path to .data section', type=str)
    args = parser.parse_args()

    #TODO: check path error

    with open(args.datapath, 'rb') as f:
        f.seek(0x15abb0)
        

if __name__ == '__main__' :
    main()