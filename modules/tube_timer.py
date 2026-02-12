class TubeTimer:
    def __init__(self, dis_obj):
        self.dis = dis_obj
        self.timer = 0
        self.minutes = 0
        self.data = []

        self.heading_number = 0
        self.heading_active = 0
        self.heading_age_min = 0
        self.heading_age_hour = 0

        self.display_tube = 1

    def add_minute(self):
        self.minutes = self.minutes + 1
        print("minutes timer is", self.minutes)
        self.inc_tube_data()

    def read_tube_data(self):
        self.data.clear()
        with open("tubeData.csv", "r") as file:
            for line_str in file:
                line_str = line_str.rstrip("\n").rstrip("\r")
                self.data.append(line_str.split(","))

        for i, heading in enumerate(self.data[0]):
            if heading == "number":
                self.heading_number = i
            elif heading == "active":
                self.heading_active = i
            elif heading == "ageMin":
                self.heading_age_min = i
            elif heading == "ageHour":
                self.heading_age_hour = i

    def inc_tube_data(self):
        self.read_tube_data()
        for line_list in self.data:
            if line_list[self.heading_active] == "yes":
                tube_age_min = int(line_list[self.heading_age_min]) + 1
                line_list[self.heading_age_min] = str(tube_age_min)
                if tube_age_min >= 60:
                    line_list[self.heading_age_min] = "0"
                    line_list[self.heading_age_hour] = str(int(line_list[self.heading_age_hour]) + 1)
        self.write_tube_data()

    def write_tube_data(self):
        if not self.data:
            return

        header = self.data[0]
        rows = self.data[1:]

        def tube_key(row):
            try:
                return int(row[self.heading_number])
            except (ValueError, IndexError):
                return 10 ** 9

        rows.sort(key=tube_key)
        self.data = [header] + rows

        with open("tubeData.csv", "w") as output_file:
            for line_list in self.data:
                write_line = (
                    line_list[self.heading_number]
                    + ","
                    + line_list[self.heading_active]
                    + ","
                    + line_list[self.heading_age_min]
                    + ","
                    + line_list[self.heading_age_hour]
                    + "\n"
                )
                output_file.write(write_line)

    def show_tt(self, change):
        self.read_tube_data()
        tube_count = len(self.data) - 1
        if tube_count <= 0:
            return

        self.display_tube = self.display_tube + change

        if self.display_tube < 1:
            self.display_tube = 1
        if self.display_tube > tube_count:
            self.display_tube = tube_count

        line_list = self.data[self.display_tube]
        tube_num = int(line_list[self.heading_number])
        self.dis.display_tube_timer(
            tube_num,
            line_list[self.heading_active],
            line_list[self.heading_age_min],
            line_list[self.heading_age_hour],
        )

    def get_tube_record(self, tube_number):
        self.read_tube_data()
        for i, line_list in enumerate(self.data):
            if i == 0:
                continue
            tube_num = int(line_list[self.heading_number])
            if tube_num == tube_number:
                return {
                    "number": tube_num,
                    "active": line_list[self.heading_active],
                    "age_min": int(line_list[self.heading_age_min]),
                    "age_hour": int(line_list[self.heading_age_hour]),
                }
        return None

    def get_all_tube_records(self):
        self.read_tube_data()
        rows = []
        for i, line_list in enumerate(self.data):
            if i == 0:
                continue
            rows.append(
                {
                    "number": int(line_list[self.heading_number]),
                    "active": line_list[self.heading_active],
                    "age_min": int(line_list[self.heading_age_min]),
                    "age_hour": int(line_list[self.heading_age_hour]),
                }
            )
        return rows

    def set_tube_record(self, tube_number, active, age_min, age_hour):
        self.read_tube_data()
        for i, line_list in enumerate(self.data):
            if i == 0:
                continue
            tube_num = int(line_list[self.heading_number])
            if tube_num == tube_number:
                line_list[self.heading_active] = active
                line_list[self.heading_age_min] = str(age_min)
                line_list[self.heading_age_hour] = str(age_hour)
                self.write_tube_data()
                return {
                    "number": tube_num,
                    "active": line_list[self.heading_active],
                    "age_min": int(line_list[self.heading_age_min]),
                    "age_hour": int(line_list[self.heading_age_hour]),
                }
        return None

    def add_tube_record(self, tube_number, active, age_min, age_hour):
        self.read_tube_data()
        for i, line_list in enumerate(self.data):
            if i == 0:
                continue
            try:
                existing_num = int(line_list[self.heading_number])
            except (ValueError, IndexError):
                continue
            if existing_num == tube_number:
                return None

        self.data.append([str(tube_number), active, str(age_min), str(age_hour)])
        self.write_tube_data()
        return {
            "number": tube_number,
            "active": active,
            "age_min": age_min,
            "age_hour": age_hour,
        }

    def delete_tube_record(self, tube_number):
        self.read_tube_data()
        delete_index = -1
        for i, line_list in enumerate(self.data):
            if i == 0:
                continue
            if int(line_list[self.heading_number]) == tube_number:
                delete_index = i
                break

        if delete_index < 0:
            return False

        del self.data[delete_index]
        self.write_tube_data()
        return True
