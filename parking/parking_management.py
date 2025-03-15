import json
import cv2
import numpy as np
from ultralytics.solutions.solutions import BaseSolution
from ultralytics.utils import LOGGER
from ultralytics.utils.plotting import Annotator

def get_min_coords(polygon):
    """
    Extracts the minimum x and y coordinates from a polygon's vertices.
    
    This function calculates the minimum x and y values from the list of points
    defining a polygon. The returned values are primarily used for vertical
    sorting (top-to-bottom) followed by horizontal sorting (left-to-right).
    
    Parameters:
    -----------
    polygon : dict
        A dictionary containing a 'points' key. The value is a list of 2D points
        (each represented as a list of [x, y] coordinates).
    
    Returns:
    --------
    tuple
        A tuple containing:
        - min_y (float): The smallest y-coordinate among all polygon points
        - min_x (float): The smallest x-coordinate among all polygon points
        
    Example:
    --------
    For a polygon with points [[1553, 48], [1718, 40], [1735, 128], [1577, 133]]:
    >>> get_min_coords({
    ...     'points': [[1553, 48], [1718, 40], [1735, 128], [1577, 133]]
    ... })
    (40, 1553)
    
    Note:
    -----
    The order of return values (min_y first) is intentional to prioritize 
    vertical sorting over horizontal sorting when used as a key function.
    """
    points = polygon['points']
    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    return min_y, min_x

def round_invoice(amount):
    """
    Rounds the invoice amount to the nearest lower multiple of 100.

    Args:
        amount (int): The invoice amount to be rounded. For decimal values, 
                      convert to an integer first (e.g., using `int()`).

    Returns:
        int: The rounded amount to the nearest lower multiple of 100.

    Examples:
        >>> round_invoice(2335)
        2300
        >>> round_invoice(2578)
        2500
        >>> round_invoice(2999)
        2900
        >>> round_invoice(3000)
        3000
        >>> round_invoice(99)
        0

    Notes:
        - If the amount is less than 100, it will be rounded down to 0.
        - Uses integer division to truncate the value after dividing by 100.
        - To handle decimal amounts (e.g., 2335), convert to integer first:
          `round_invoice(int(2335))` → 2300.
    """
    return (amount // 100) * 100

def calc_invoice(time, price_per_hour):
    """
    Calculates the invoice amount based on the time spent and the hourly rate.

    Args:
        time (float): The time spent in minutes (e.g., 30 for 30 minutes).
        price_per_hour (float): The cost per hour (e.g., 6000 for 6000 SYP/hour).

    Returns:
        float: The calculated invoice amount after converting the hourly rate to a per-minute basis.

    Examples:
        >>> calc_invoice(30, 6000)  # 30 minutes at 6000 SYP/hour → (6000/60)*30 = 3000 SYP
        50.0
        >>> calc_invoice(45, 12000)  # 45 minutes at 12000 SYP/hour → (12000/60)*45 = 9000 SYP
        90.0
        >>> calc_invoice(0, 8000)    # 0 minutes → 0 SYP
        0.0

    Notes:
        - Assumes `time` is provided in minutes. If `time` is in hours, multiply by 60 first.
        - The result is a float. Use `round()` if you need to limit decimal places.
        - Negative values for `time` or `price_per_hour` will produce negative results.
    """
    # return price_per_hour * time

    return (price_per_hour / 60) * time

def draw_polygon_with_number(image, pts_array, is_occupied, number, occupied_color, available_color):
    """
    Draws a polygon on the image and adds a number label above it
    
    Parameters:
        image (numpy.ndarray): Input image
        pts_array (numpy.ndarray): Polygon coordinates (shape: [N, 2])
        is_occupied (bool): Determines if the polygon is occupied
        number (int/str): Number/text to display
        occupied_color (tuple): BGR color for occupied state
        available_color (tuple): BGR color for available state
    """
    # Draw polygon
    color = occupied_color if is_occupied else available_color
    cv2.polylines(image, [pts_array], isClosed=True, color=color, thickness=1)

    # Calculate text position (top-left corner with offset)
    x_coords = pts_array[0][:, 0]
    y_coords = pts_array[0][:, 1]
    x_min, y_min = np.min(x_coords), np.min(y_coords)
    text_position = (x_min, y_min - 10)
    
    # Add text label
    cv2.putText(
        image,
        text=str(number),
        org=text_position,
        fontFace=cv2.FONT_HERSHEY_DUPLEX,
        fontScale=0.8,
        color=color,
        thickness=2,
        lineType=cv2.LINE_AA
    )

class ParkingManagement(BaseSolution):
    """
    Manages parking occupancy and availability using YOLO model for real-time monitoring and visualization.

    This class extends BaseSolution to provide functionality for parking lot management, including detection of
    occupied spaces, visualization of parking regions, and display of occupancy statistics.

    Attributes:
        json_file (str): Path to the JSON file containing parking region details.
        json (List[Dict]): Loaded JSON data containing parking region information.
        pr_info (Dict[str, int]): Dictionary storing parking information (Occupancy and Available spaces).
        arc (Tuple[int, int, int]): RGB color tuple for available region visualization.
        occ (Tuple[int, int, int]): RGB color tuple for occupied region visualization.
        dc (Tuple[int, int, int]): RGB color tuple for centroid visualization of detected objects.
        price_per_hour (float): Price per hour for parking.
        spots (Dict[int, Dict]): Dictionary to store parking spots information.

    Methods:
        process_data: Processes model data for parking lot management and visualization.

    Examples:
        >>> from ultralytics.solutions import ParkingManagement
        >>> parking_manager = ParkingManagement(model="yolo11n.pt", json_file="parking_regions.json", price_per_hour=10.0)
        >>> print(f"Occupied spaces: {parking_manager.pr_info['Occupancy']}")
        >>> print(f"Available spaces: {parking_manager.pr_info['Available']}")
    """

    def __init__(self, price_per_hour=None, **kwargs):
        """Initializes the parking management system with a YOLO model, visualization settings, and price per hour."""
        super().__init__(**kwargs)

        self.json_file = self.CFG["json_file"]  # Load JSON data
        if self.json_file is None:
            LOGGER.warning("❌ json_file argument missing. Parking region details required.")
            raise ValueError("❌ Json file path can not be empty")

        with open(self.json_file) as f:
            self.json = json.load(f)

        self.pr_info = {"Occupancy": 0, "Available": 0, 'total_cars':0, 'total_time':0, 'total_revenue':0}  # dictionary for parking information

        self.arc = (0, 0, 255)  # available region color
        self.occ = (0, 255, 0)  # occupied region color
        self.dc = (255, 0, 189)  # centroid color for each box

        self.price_per_hour = price_per_hour  # Store price per hour
        self.spots = dict()

        for idx in range(len(self.json)):
            self.spots[idx+1] = {'Time':0,'Invoice':0, 'IsAvailable': True}

    def process_data(self, im0):
        """
        Processes the model data for parking lot management.

        This function analyzes the input image, extracts tracks, and determines the occupancy status of parking
        regions defined in the JSON file. It annotates the image with occupied and available parking spots,
        and updates the parking information.

        Args:
            im0 (np.ndarray): The input inference image.

        Examples:
            >>> parking_manager = ParkingManagement(json_file="parking_regions.json")
            >>> image = cv2.imread("parking_lot.jpg")
            >>> parking_manager.process_data(image)
        """
        self.extract_tracks(im0)  # extract tracks from im0
        es, fs = len(self.json), 0  # empty slots, filled slots
        annotator = Annotator(im0, self.line_width)  # init annotator

        for idx,region in enumerate(self.json):
            # Convert points to a NumPy array with the correct dtype and reshape properly
            pts_array = np.array(region["points"], dtype=np.int32).reshape((-1, 1, 2))
            rg_occupied = False  # occupied region initialization
            for box, cls in zip(self.boxes, self.clss):
                xc, yc = int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2)
                dist = cv2.pointPolygonTest(pts_array, (xc, yc), False)
                if dist >= 0:
                    # cv2.circle(im0, (xc, yc), radius=self.line_width * 4, color=self.dc, thickness=-1)
                    annotator.display_objects_labels(
                        im0, self.model.names[int(cls)], (104, 31, 17), (255, 255, 255), xc, yc, 10
                    )
                    rg_occupied = True
                    break
            fs, es = (fs + 1, es - 1) if rg_occupied else (fs, es)
            # Plotting regions
            # cv2.polylines(im0, [pts_array], isClosed=True, color=self.occ if rg_occupied else self.arc, thickness=1)
            draw_polygon_with_number(image=im0,
                                     pts_array=pts_array,
                                     is_occupied=rg_occupied,  # Change to True to see color change
                                     number=idx+1,
                                     occupied_color=self.occ,  # Red for occupied
                                     available_color=self.arc  # Green for available
                                    )
            # Previous Available and Current Available do not make any thing
            if self.spots[idx+1]['IsAvailable'] and not rg_occupied:
                pass

            # Previous Available and Current Not Available do (total cars + 1) and set Current to Previous
            if self.spots[idx+1]['IsAvailable'] and rg_occupied:
                self.pr_info['total_cars'] += 1

                self.spots[idx+1]['IsAvailable'] = False

            # Previous Not Available and Current Available do (total time + time, time -> 0, total_revenu + invoice, invoice -> 0) and set Current to Previous
            if not self.spots[idx+1]['IsAvailable'] and not rg_occupied:
                self.pr_info['total_time'] += self.spots[idx+1]['Time']
                self.spots[idx+1]['Time'] = 0

                self.pr_info['total_revenue'] += round_invoice(self.spots[idx+1]['Invoice'])
                self.spots[idx+1]['Invoice'] = 0

                self.spots[idx+1]['IsAvailable'] = True

            # Previous Not Available and Current Not Available do (time + 1, invoice + price)
            if not self.spots[idx+1]['IsAvailable'] and rg_occupied:
                self.spots[idx+1]['Time'] += 1
                self.spots[idx+1]['Invoice'] = calc_invoice(time=self.spots[idx+1]['Time'], price_per_hour=self.price_per_hour)


        self.pr_info["Occupancy"], self.pr_info["Available"] = fs, es

        # annotator.display_analytics(im0, self.pr_info, (104, 31, 17), (255, 255, 255), 10)
        self.display_output(im0)  # display output with base class function
        return im0  # return output image for more usage