import { GET_STUDENT } from '../constants/index';

const studentReducer = (studentInfo = {}, action) => {
  switch (action.type) {
    case GET_STUDENT:
      return action.payload;
    default:
      return studentInfo;
  }
}

export default studentReducer;