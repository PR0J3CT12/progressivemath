import { combineReducers } from 'redux';

import auth from './auth';
import studentReducer from "./student";

export const reducers = combineReducers({ auth, studentReducer });