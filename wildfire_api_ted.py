"""
wildfire_api_ted.py

Api for widfire panel

data: https://catalog.data.gov/dataset/odf-fire-occurrence-data-2000-2022/resource/abea76e1-43bf-488d-863a-ba7af6c1b0e9
"""
import pandas as pd


class FIREAPI:
    def __init__(self):
        self.fire_df = None

    def load_data(self, file):
        """Loads the csv data and cleans it"""
        # load file into instance variable
        self.fire_df = pd.read_csv(file)

        # create a copy to work with
        fire_df = self.fire_df[["FireYear", "EstTotalAcres",
                                "HumanOrLightning", "CauseBy",
                                "Lat_DD", "Long_DD"]].copy()
        # drop missing or empty data rows
        fire_df = fire_df.dropna()
        # creating simple names for ease of use
        rename = {"FireYear": "year",
                   "EstTotalAcres": "acres",
                   "HumanOrLightning": "HumanOrLightning",
                   "CauseBy": "cause",
                   "Lat_DD": "lat",
                   "Long_DD": "lon"}
        fire_df = fire_df.rename(columns= rename)

        # converting numerical data to floats
        to_convert = ["year", "acres", "lat", "lon"]
        for val in to_convert:
            fire_df[val] = pd.to_numeric(fire_df[val], errors= "coerce")
        # im removing fires with 0 acres of damage
        fire_df = fire_df[fire_df["acres"] > 0].copy()
        # sort by year ascending
        fire_df = fire_df.sort_values("year", ascending=True)
        # remove index column and update instance variable
        self.fire_df = fire_df.reset_index(drop= True)

    def human_df(self):
        """Returns fire_df with only rows where the fire was caused by
        humans."""
        df = self.fire_df.copy()
        human_df = df[df["HumanOrLightning"] == "Human"].copy()
        return human_df

    def lightning_df(self):
        """Returns fire_df with only rows caused by lightning"""
        df = self.fire_df.copy()
        light_df = df[df["HumanOrLightning"] == "Lightning"].copy()
        return light_df

    def filter_by_cause(self, df, causes=None):
        """
        takes a df returns filtered df where only inputted causes show up
        """
        # if no causes provided, return a copy of the original df
        if not causes:
            return df.copy()

        # convert to strings so matching is consistent
        cause_series = df["cause"].astype(str)

        # keep only rows whose cause is in causes
        filtered = df[cause_series.isin([str(cause) for cause in
                                         causes])].copy()

        # removes index
        filtered_final = filtered.reset_index(drop=True)

        return filtered_final

    def return_dataframe(self):
        """returns a copy of fire_df"""
        df = self.fire_df.copy()
        return df


    def print_data(self):
        """prints fire_df"""
        print(self.fire_df)


def main():
    fireapi = FIREAPI()
    fireapi.load_data("data/ODF_Fire_Occurrence_Data_2000-2022.csv")
    # testing
    fireapi.print_data()





if __name__ == "__main__":
    main()