import React from "react";
import { Grid, Paper, Typography } from '@mui/material';
import {
    School as SchoolIcon,
    People as PeopleIcon,
    LibraryBooks as LibraryIcon,
    MonetizationOn as FinanceIcon
} from '@mui/icons-material';

const stats =[
    { title: 'Total Students', value: '12,345', icon: <PeopleIcon fontSize="large" /> },
    { title: 'Faculty Members', value: '1,234', icon: <SchoolIcon fontSize="large" /> },
    { title: 'Courses Offered', value: '256', icon: <LibraryIcon fontSize="large" /> },
    { title: 'Annual Budget', value: '$125M', icon: <FinanceIcon fontSize="large" /> },
];

export default function Dashboard() {
    return (
        <div>
            <Typography variant="h4" gutterBottom>
                University Dashboard
            </Typography>

            <Grid container spacing={3}>
                {stats.map((stat, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                        <Paper sx={{ p: 3, display: 'flex', alignItems: 'center' }}>
                            <div style={{ marginRight: 16, color: '#003366' }}>
                                {stat.icon}
                            </div>
                            <div>
                                <Typography variant="h6">{stat.value}</Typography>
                                <Typography variant="subtitle2">{stat.title}</Typography>
                            </div>
                        </Paper>
                    </Grid>
                ))}

                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3, height: 300 }}>
                        <Typography variant="h6" gutterBottom>
                            Enrollment Trends
                        </Typography>
                            {/* Placeholder for chart */}
                        <div style={{ 
                            backgroundColor: '#f5f5f5', 
                            height: '80%', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center' 
                            }}>
                            <Typography>Chart Component</Typography>
                        </div>
                    </Paper>
                </Grid>

                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, height: 300 }}>
                        <Typography variant="h6" gutterBottom>
                            Recent Announcements
                        </Typography>
                        {/* Announcements list would go here */}
                    </Paper>
                </Grid>
            </Grid>
        </div>
    );
}