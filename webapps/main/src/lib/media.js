export function getPicPath(operator) {
  let user_pic_folder = '/media/user/'
  let filename = (operator.name + operator.surname).replace(/\s+/,'').toLowerCase()
  return user_pic_folder + filename + '.jpg'
}