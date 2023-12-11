// function updateListItemByKeyOld(list, key, func) {
// 	for (let i in list) {
// 		if (list[i]._key === key) {
// 			func(list[i])
// 			break
// 		}
// 	}
// }

// Other possible implementation with .find()

function updateListItemByKey(list, key, func) {
  func(list.find((el) => el._key === key));
}

export { updateListItemByKey };
