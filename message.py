# # def create_message_flags(is_compressed: bool = False) -> int:
# #     flags = 0
# #     if is_compressed:
# #         flags ^= 0b00000001
# #     return flags

# class MessageFlags:
#     is_compressed: bool

#     def as_int(self) -> int:
#         flags = 0
#         if self.is_compressed:
#             flags ^= 1
#         return flags

#     @staticmethod
#     def read(flag: int) -> 'MessageFlags':
#         is_compressed = flag & 1:
