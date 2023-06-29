# originally script from LCS

# def get_epoch(train_steps: int, train_examples: int, wanted_epoch: int):
#   train_steps = 50000
#   for x in range(0, 100):
#     y = train_steps * x // train_examples
#     if y == wanted_epoch:
#       return x
#   return None

def _check_epoch_value(train_steps: int, train_examples: int, wanted_epoch: int, x: int):
  if x * train_steps // train_examples == wanted_epoch:
    return True
  return False

def get_epoch(train_steps: int, train_examples: int, wanted_epoch: int):
  if train_steps <= 0 or train_examples <= 0:
    raise ValueError("Both train_steps and train_examples should be positive integers")

  x = wanted_epoch * train_examples // train_steps

  # Verify that x indeed leads to the wanted_epoch
  if _check_epoch_value(train_steps, train_examples, wanted_epoch, x):
    return x
  # If not, try to find a value of x in range x-10 ~ x+10
  for i in range(1, 11):
    if _check_epoch_value(train_steps, train_examples, wanted_epoch, x-i):
      return x-i
    if _check_epoch_value(train_steps, train_examples, wanted_epoch, x+i):
      return x+i

  raise ValueError(f"Could not find a value of x such that {wanted_epoch} epochs could be achieved with given train_steps and train_examples")
