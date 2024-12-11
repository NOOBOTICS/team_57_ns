import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from tf2_ros import Buffer, TransformListener,tf2_ros
from geometry_msgs.msg import TransformStamped

class MapMergerNode(Node):
    def __init__(self):
        super().__init__('map_merger_node')

        # Initialize map sub
        self.map_sub1 = self.create_subscription(OccupancyGrid, '/robot1/map', self.map_callback, 10)
        self.map_sub2 = self.create_subscription(OccupancyGrid, '/robot2/map', self.map_callback, 10)
        self.map_sub3 = self.create_subscription(OccupancyGrid, '/robot3/map', self.map_callback, 10)
        
        # Initialize buffer 
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Publisher for merged map
        self.merged_map_pub = self.create_publisher(OccupancyGrid, '/merged_map', 10)

    def map_callback(self, msg):
        # Transform the map to the global frame 
        try:
            transform = self.tf_buffer.lookup_transform('global_map', msg.header.frame_id, rclpy.time.Time())
            transformed_map = self.transform_map(msg, transform)
            self.merge_map(transformed_map)
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
            self.get_logger().info("Transform not available yet")

    def transform_map(self, map_msg, transform):
        ###
        transformed_map = OccupancyGrid()
        transformed_map.header = map_msg.header
        transformed_map.info = map_msg.info  ###

        
        for i in range(map_msg.info.width):
            for j in range(map_msg.info.height):
                # Convert map grid coordinates (i, j) to world coordinates (x, y)
                world_x = i * map_msg.info.resolution + map_msg.info.origin.position.x
                world_y = j * map_msg.info.resolution + map_msg.info.origin.position.y
                
                
                transformed_x, transformed_y = self.apply_transform_to_coordinates(world_x, world_y, transform)
                
                ###
                map_x, map_y = self.convert_to_map_coordinates(transformed_x, transformed_y, map_msg)
                
                # Set the occupancy value at the new map coordinates
                transformed_map.data[map_y * map_msg.info.width + map_x] = map_msg.data[j * map_msg.info.width + i]
        
        return transformed_map


    def merge_map(self, map_msg):
        # merged map in self.merged_map
        if not hasattr(self, 'merged_map'):
            self.merged_map = map_msg  # Initialize with the first map

        
        ###
        for i in range(len(map_msg.data)):
            if map_msg.data[i] != -1:  # Ignore unknown cells
                if self.merged_map.data[i] == -1: 
                    self.merged_map.data[i] = map_msg.data[i]
                else:
                    # weighted averaging
                    self.merged_map.data[i] = (self.merged_map.data[i] + map_msg.data[i]) // 2

        self.get_logger().info("Merged maps")
        self.merged_map_pub.publish(self.merged_map)

def main(args=None):
    rclpy.init(args=args)
    map_merger = MapMergerNode()
    rclpy.spin(map_merger)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
