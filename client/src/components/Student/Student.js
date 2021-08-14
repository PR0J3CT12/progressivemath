import React from 'react';
import {Redirect, useParams} from 'react-router-dom';

let isAuthorized = (id) => {
    let profile = JSON.parse(localStorage.getItem('profile'));

    if (profile.user_id == id) {
        return true;
    } else {
        return false;
    }
}

const Student = () => {
    let { id } = useParams();

    const isAuth = isAuthorized(id);

    if (isAuth) {
        return (
            <div>test</div>
        );
    } else {
        return (
            <Redirect to="/auth"/>
        )
    }
};


export default Student;