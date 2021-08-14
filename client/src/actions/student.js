import { GET_STUDENT } from "../constants";

import * as api from '../api/index';

export const getStudent = (studentId) => async (dispatch) => {
	try {
		const { data } = await api.getStudent(studentId);

		dispatch({ type: GET_STUDENT, data });

	} catch (err) {
		console.log(err);
	}
};
