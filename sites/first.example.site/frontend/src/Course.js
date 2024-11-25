import React, { useState, useEffect } from "react";
import { useKeycloak } from "@react-keycloak/web";
import "./styles/Course.css";  // Import the CSS file

const Course = () => {
  const { keycloak } = useKeycloak();
  const [courseData, setCourseData] = useState(null);  // To store course data
  const [errorMessage, setErrorMessage] = useState("");  // To store error messages
  const [loading, setLoading] = useState(true);  // To manage loading state

  useEffect(() => {
    // Function to fetch course data from the API
    const fetchCourseData = async () => {
      try {
        const token = keycloak.token;  // Assuming the token is stored in localStorage
        if (!token) {
          setErrorMessage("No token available. Please login.");
          setLoading(false);
          return;
        }

        const response = await fetch("http://localhost:5001/api/resource", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          // Handle different status codes
          if (response.status === 401) {
            setErrorMessage("Unauthorized. Invalid or expired token.");
          } else if (response.status === 403) {
            setErrorMessage("Forbidden. Insufficient permissions.");
          } else {
            setErrorMessage("An unexpected error occurred.");
          }
        } else {
          const data = await response.json();
          if (data.data) {
            setCourseData(data.data);  // Set the course data to state
          } else {
            setErrorMessage("No course data found.");
          }
        }
      } catch (error) {
        setErrorMessage("Error fetching course data: " + error.message);
      } finally {
        setLoading(false);  // Set loading to false when the request finishes
      }
    };

    fetchCourseData();  // Call the function when the component mounts
  }, [keycloak.token]);

  if (loading) {
    return <div className="loading-message">Loading...</div>;  // Show loading message while fetching data
  }

  if (errorMessage) {
    return <div className="error-message"><h2>Error</h2><p>{errorMessage}</p></div>;  // Show error message
  }

  if (courseData) {
    return (
      <div className="course-container">
        <h2 className="course-title">Your Course Information</h2>
        <div>
          <p className="course-info"><span className="bold-text">Major:</span> {courseData.major}</p>
          <p className="course-info"><span className="bold-text">Enrollment Date:</span> {courseData.enrollment_date}</p>
          <p className="course-info"><span className="bold-text">Expected Graduation:</span> {courseData.expected_graduation}</p>
          <p className="course-info"><span className="bold-text">GPA:</span> {courseData.gpa}</p>
          <p className="course-info"><span className="bold-text">Credits Completed:</span> {courseData.credits_completed}</p>
          {/* Add more fields based on the course data */}
        </div>
      </div>
    );
  }

  return null;  // If there's no data or error, render nothing
};

export default Course;
