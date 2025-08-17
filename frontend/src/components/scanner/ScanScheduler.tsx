'use client';

import { useState, useEffect } from 'react';
import { ScanConfig } from '@/types/scanner';

interface ScheduledScan {
  id: string;
  name: string;
  config: ScanConfig;
  frequency: 'once' | 'hourly' | 'daily' | 'weekly';
  time?: string; // HH:MM format
  daysOfWeek?: number[]; // 0-6 for Sunday-Saturday
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
}

interface ScanSchedulerProps {
  currentConfig: ScanConfig;
}

export default function ScanScheduler({ currentConfig }: ScanSchedulerProps) {
  const [schedules, setSchedules] = useState<ScheduledScan[]>([]);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [newSchedule, setNewSchedule] = useState<Partial<ScheduledScan>>({
    frequency: 'daily',
    time: '09:30',
    enabled: true,
    daysOfWeek: [1, 2, 3, 4, 5], // Weekdays
  });

  const daysOfWeek = [
    { value: 0, label: 'Sun' },
    { value: 1, label: 'Mon' },
    { value: 2, label: 'Tue' },
    { value: 3, label: 'Wed' },
    { value: 4, label: 'Thu' },
    { value: 5, label: 'Fri' },
    { value: 6, label: 'Sat' },
  ];

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = () => {
    const saved = localStorage.getItem('scanSchedules');
    if (saved) {
      setSchedules(JSON.parse(saved));
    }
  };

  const saveSchedule = () => {
    if (!newSchedule.name) return;

    const schedule: ScheduledScan = {
      id: `schedule_${Date.now()}`,
      name: newSchedule.name || '',
      config: currentConfig,
      frequency: newSchedule.frequency || 'daily',
      time: newSchedule.time,
      daysOfWeek: newSchedule.daysOfWeek,
      enabled: true,
      nextRun: calculateNextRun(newSchedule.frequency || 'daily', newSchedule.time, newSchedule.daysOfWeek),
    };

    const updated = [...schedules, schedule];
    setSchedules(updated);
    localStorage.setItem('scanSchedules', JSON.stringify(updated));
    
    setShowScheduleDialog(false);
    setNewSchedule({
      frequency: 'daily',
      time: '09:30',
      enabled: true,
      daysOfWeek: [1, 2, 3, 4, 5],
    });
  };

  const toggleSchedule = (id: string) => {
    const updated = schedules.map(s => 
      s.id === id ? { ...s, enabled: !s.enabled } : s
    );
    setSchedules(updated);
    localStorage.setItem('scanSchedules', JSON.stringify(updated));
  };

  const deleteSchedule = (id: string) => {
    const updated = schedules.filter(s => s.id !== id);
    setSchedules(updated);
    localStorage.setItem('scanSchedules', JSON.stringify(updated));
  };

  const calculateNextRun = (frequency: string, time?: string, days?: number[]): string => {
    const now = new Date();
    let next = new Date();

    if (time) {
      const [hours, minutes] = time.split(':').map(Number);
      next.setHours(hours, minutes, 0, 0);
    }

    switch (frequency) {
      case 'hourly':
        next.setHours(next.getHours() + 1);
        break;
      case 'daily':
        if (next <= now) {
          next.setDate(next.getDate() + 1);
        }
        break;
      case 'weekly':
        if (days && days.length > 0) {
          // Find next day in schedule
          let daysAhead = 0;
          for (let i = 1; i <= 7; i++) {
            const checkDay = (now.getDay() + i) % 7;
            if (days.includes(checkDay)) {
              daysAhead = i;
              break;
            }
          }
          next.setDate(next.getDate() + daysAhead);
        }
        break;
    }

    return next.toLocaleString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Scheduled Scans
        </h3>
        <button
          onClick={() => setShowScheduleDialog(true)}
          className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
        >
          + Add Schedule
        </button>
      </div>

      {schedules.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm">No scheduled scans</p>
          <p className="text-xs mt-1">Create a schedule to automate scanning</p>
        </div>
      ) : (
        <div className="space-y-3">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                      {schedule.name}
                    </h4>
                    <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                      schedule.enabled 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {schedule.enabled ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 space-y-1">
                    <div>Frequency: {schedule.frequency}</div>
                    {schedule.time && <div>Time: {schedule.time}</div>}
                    {schedule.frequency === 'weekly' && schedule.daysOfWeek && (
                      <div>
                        Days: {schedule.daysOfWeek.map(d => 
                          daysOfWeek.find(day => day.value === d)?.label
                        ).join(', ')}
                      </div>
                    )}
                    {schedule.nextRun && (
                      <div>Next run: {schedule.nextRun}</div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => toggleSchedule(schedule.id)}
                    className={`text-sm ${
                      schedule.enabled 
                        ? 'text-yellow-600 hover:text-yellow-800'
                        : 'text-green-600 hover:text-green-800'
                    }`}
                  >
                    {schedule.enabled ? 'Pause' : 'Enable'}
                  </button>
                  <button
                    onClick={() => deleteSchedule(schedule.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Schedule Dialog */}
      {showScheduleDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Schedule Scan
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Schedule Name
                </label>
                <input
                  type="text"
                  value={newSchedule.name || ''}
                  onChange={(e) => setNewSchedule({ ...newSchedule, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  placeholder="Morning Scan"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Frequency
                </label>
                <select
                  value={newSchedule.frequency}
                  onChange={(e) => setNewSchedule({ ...newSchedule, frequency: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="once">Once</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>

              {(newSchedule.frequency === 'daily' || newSchedule.frequency === 'weekly') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Time
                  </label>
                  <input
                    type="time"
                    value={newSchedule.time}
                    onChange={(e) => setNewSchedule({ ...newSchedule, time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
              )}

              {newSchedule.frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Days of Week
                  </label>
                  <div className="flex space-x-2">
                    {daysOfWeek.map(day => (
                      <label key={day.value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newSchedule.daysOfWeek?.includes(day.value)}
                          onChange={(e) => {
                            const days = newSchedule.daysOfWeek || [];
                            if (e.target.checked) {
                              setNewSchedule({ ...newSchedule, daysOfWeek: [...days, day.value] });
                            } else {
                              setNewSchedule({ ...newSchedule, daysOfWeek: days.filter(d => d !== day.value) });
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-1 text-xs">{day.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setShowScheduleDialog(false)}
                  className="px-4 py-2 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSchedule}
                  className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Save Schedule
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}