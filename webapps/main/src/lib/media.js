export function getPicPath(operator) {
  let user_pic_folder = '/media/user/'
  // use concat on empty string to avoid errors if no operator is passed
  let filename = ''.concat(operator.name, operator.surname).replace(/\s+/,'').toLowerCase()
  return user_pic_folder + filename + '.jpg'
}