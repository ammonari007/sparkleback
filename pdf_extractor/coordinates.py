import fitz

def in_rect(parent_rect, child_rect):
  if parent_rect.contains(child_rect):
    return "contains"
  elif parent_rect.intersects(child_rect):
    return "overlap"

def rect_inte
