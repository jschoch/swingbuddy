from util import run_predf_pipes, load_pipes



if __name__ == "__main__":
    processors = load_pipes()
    data = "Sample Data"

    df = run_predf_pipes()
    print(df.to_dict())