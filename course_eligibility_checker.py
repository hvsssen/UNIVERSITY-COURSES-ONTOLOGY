#!/usr/bin/env python3
"""
University Course Eligibility Checker
=====================================
Practical Application for University Courses Ontology
Team: Slim Hassen & Khalifa Abdallah

This script demonstrates the practical value of the ontology by:
1. Checking which courses a student can enroll in
2. Finding prerequisite chains for advanced courses
3. Generating professor workload reports

Requirements:
    pip install rdflib
"""

from rdflib import Graph, Namespace, RDF, RDFS
from typing import List, Dict, Set

# Define namespace
ONTO = Namespace("http://www.semanticweb.org/university/ontology#")


class CourseEligibilityChecker:
    """Check student eligibility for courses based on completed prerequisites."""
    
    def __init__(self, owl_file: str):
        """Load the ontology from OWL file."""
        self.g = Graph()
        self.g.parse(owl_file, format='xml')
        self.g.bind('onto', ONTO)
        
    def get_courses_taken(self, student_id: str) -> Set[str]:
        """Get all courses a student has completed."""
        query = f"""
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT ?courseCode
        WHERE {{
            :{student_id} :hasTaken ?course .
            ?course :courseCode ?courseCode .
        }}
        """
        results = self.g.query(query)
        return {str(row.courseCode) for row in results}
    
    def get_prerequisites(self, course_code: str) -> List[str]:
        """Get all prerequisites (direct and indirect) for a course."""
        query = f"""
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT DISTINCT ?prereqCode
        WHERE {{
            ?course :courseCode "{course_code}" .
            ?course :hasPrerequisite+ ?prereq .
            ?prereq :courseCode ?prereqCode .
        }}
        """
        results = self.g.query(query)
        return [str(row.prereqCode) for row in results]
    
    def get_direct_prerequisites(self, course_code: str) -> List[str]:
        """Get only direct prerequisites for a course."""
        query = f"""
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT ?prereqCode
        WHERE {{
            ?course :courseCode "{course_code}" .
            ?course :hasPrerequisite ?prereq .
            ?prereq :courseCode ?prereqCode .
        }}
        """
        results = self.g.query(query)
        return [str(row.prereqCode) for row in results]
    
    def can_enroll(self, student_id: str, course_code: str) -> tuple[bool, List[str]]:
        """
        Check if student can enroll in a course.
        Returns: (can_enroll: bool, missing_prerequisites: List[str])
        """
        courses_taken = self.get_courses_taken(student_id)
        prerequisites = set(self.get_prerequisites(course_code))
        
        # If no prerequisites, can enroll
        if not prerequisites:
            return True, []
        
        # Check if all prerequisites are satisfied
        missing = prerequisites - courses_taken
        return len(missing) == 0, sorted(list(missing))
    
    def get_available_courses(self, student_id: str) -> List[Dict]:
        """Get all courses a student can currently enroll in."""
        query = """
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT ?courseCode ?courseName ?credits
        WHERE {
            ?course a :Course .
            ?course :courseCode ?courseCode .
            ?course :courseName ?courseName .
            ?course :creditHours ?credits .
        }
        """
        results = self.g.query(query)
        
        available = []
        courses_taken = self.get_courses_taken(student_id)
        
        for row in results:
            course_code = str(row.courseCode)
            
            # Skip if already taken
            if course_code in courses_taken:
                continue
            
            # Check eligibility
            can_take, missing = self.can_enroll(student_id, course_code)
            if can_take:
                available.append({
                    'code': course_code,
                    'name': str(row.courseName),
                    'credits': int(row.credits)
                })
        
        return available
    
    def get_professor_workload(self) -> List[Dict]:
        """Generate professor workload report."""
        query = """
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT ?profName ?deptName (COUNT(?course) as ?courseCount)
        WHERE {
            ?prof a :Professor .
            ?prof :professorName ?profName .
            ?prof :worksInDepartment ?dept .
            ?dept :departmentName ?deptName .
            ?course :taughtBy ?prof .
        }
        GROUP BY ?profName ?deptName
        ORDER BY DESC(?courseCount)
        """
        results = self.g.query(query)
        
        workload = []
        for row in results:
            workload.append({
                'professor': str(row.profName),
                'department': str(row.deptName),
                'courses': int(row.courseCount)
            })
        
        return workload
    
    def get_course_info(self, course_code: str) -> Dict:
        """Get detailed information about a course."""
        query = f"""
        PREFIX : <http://www.semanticweb.org/university/ontology#>
        SELECT ?courseName ?credits ?profName ?deptName
        WHERE {{
            ?course :courseCode "{course_code}" .
            ?course :courseName ?courseName .
            ?course :creditHours ?credits .
            OPTIONAL {{ 
                ?course :taughtBy ?prof .
                ?prof :professorName ?profName .
            }}
            OPTIONAL {{
                ?course :belongsToDepartment ?dept .
                ?dept :departmentName ?deptName .
            }}
        }}
        """
        results = list(self.g.query(query))
        
        if not results:
            return None
        
        row = results[0]
        direct_prereqs = self.get_direct_prerequisites(course_code)
        all_prereqs = self.get_prerequisites(course_code)
        
        return {
            'code': course_code,
            'name': str(row.courseName),
            'credits': int(row.credits),
            'professor': str(row.profName) if row.profName else 'N/A',
            'department': str(row.deptName) if row.deptName else 'N/A',
            'direct_prerequisites': direct_prereqs,
            'all_prerequisites': all_prereqs
        }


def main():
    """Demo of the course eligibility checker."""
    
    print("=" * 60)
    print("UNIVERSITY COURSE ELIGIBILITY CHECKER")
    print("Team: Slim Hassen & Khalifa Abdallah")
    print("=" * 60)
    print()
    
    # Load ontology
    owl_file = "UniversityOntology_COMPLETE.owl"
    checker = CourseEligibilityChecker(owl_file)
    
    # Example 1: Check what courses Alice can take
    print("EXAMPLE 1: Course Eligibility Check")
    print("-" * 60)
    student_id = "Student001"  # Alice
    
    courses_taken = checker.get_courses_taken(student_id)
    print(f"Student: Alice Johnson (ID: {student_id})")
    print(f"Courses Completed: {', '.join(sorted(courses_taken))}")
    print()
    
    available = checker.get_available_courses(student_id)
    print(f"Available Courses to Enroll ({len(available)} courses):")
    print()
    
    for course in available:
        print(f"  • {course['code']}: {course['name']} ({course['credits']} credits)")
    
    print()
    print()
    
    # Example 2: Analyze a specific course
    print("EXAMPLE 2: Course Prerequisite Analysis")
    print("-" * 60)
    course_code = "CS-401"
    info = checker.get_course_info(course_code)
    
    if info:
        print(f"Course: {info['code']} - {info['name']}")
        print(f"Credits: {info['credits']}")
        print(f"Professor: {info['professor']}")
        print(f"Department: {info['department']}")
        print()
        print("Direct Prerequisites:")
        for prereq in info['direct_prerequisites']:
            print(f"  • {prereq}")
        print()
        print("All Prerequisites (including indirect):")
        for prereq in info['all_prerequisites']:
            print(f"  • {prereq}")
        print()
        
        # Check if Alice can take this course
        can_take, missing = checker.can_enroll(student_id, course_code)
        print(f"Can Alice enroll? {'YES ✓' if can_take else 'NO ✗'}")
        if not can_take:
            print(f"Missing prerequisites: {', '.join(missing)}")
    
    print()
    print()
    
    # Example 3: Professor workload report
    print("EXAMPLE 3: Professor Workload Report")
    print("-" * 60)
    workload = checker.get_professor_workload()
    
    print(f"{'Professor':<30} {'Department':<20} {'Courses':<10}")
    print("-" * 60)
    for prof in workload:
        print(f"{prof['professor']:<30} {prof['department']:<20} {prof['courses']:<10}")
    
    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
