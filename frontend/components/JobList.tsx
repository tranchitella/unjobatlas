"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useState } from "react";

interface Job {
  id: string;
  post_number: string;
  post_name: string;
  organization: {
    name: string;
    abbreviation: string;
  };
  location_country: string;
  location_city?: string;
  position_level?: string;
  contract_type: string;
  application_deadline: string;
  brief_description?: string;
  is_active: boolean;
}

interface JobListProps {
  filters: any;
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
}

export function JobList({ filters, selectedJobId, onSelectJob }: JobListProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch jobs from API based on filters
    // For now, show mock data
    setLoading(false);
    setJobs([
      {
        id: "1",
        post_number: "12345",
        post_name: "Programme Officer - Child Protection",
        organization: {
          name: "UNICEF",
          abbreviation: "UNICEF",
        },
        location_country: "Kenya",
        location_city: "Nairobi",
        position_level: "P-3",
        contract_type: "fixed_term",
        application_deadline: "2025-12-31",
        brief_description:
          "The Programme Officer will support UNICEF's child protection initiatives in Kenya...",
        is_active: true,
      },
      {
        id: "2",
        post_number: "12346",
        post_name: "Emergency Coordinator",
        organization: {
          name: "World Food Programme",
          abbreviation: "WFP",
        },
        location_country: "Ethiopia",
        location_city: "Addis Ababa",
        position_level: "P-4",
        contract_type: "temporary",
        application_deadline: "2025-11-30",
        brief_description:
          "Lead emergency response operations in the Horn of Africa region...",
        is_active: true,
      },
    ]);
  }, [filters]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Loading jobs...</p>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">No jobs found matching your criteria.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Job Opportunities</h2>
        <p className="text-gray-600 mt-1">{jobs.length} positions found</p>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <Card
            key={job.id}
            className={`p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedJobId === job.id
                ? "border-blue-500 border-2 bg-blue-50"
                : "border-gray-200"
            }`}
            onClick={() => onSelectJob(job.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {job.post_name}
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  {job.organization.abbreviation || job.organization.name} •{" "}
                  {job.location_city
                    ? `${job.location_city}, ${job.location_country}`
                    : job.location_country}
                </p>
                {job.brief_description && (
                  <p className="text-sm text-gray-700 line-clamp-2 mb-3">
                    {job.brief_description}
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{job.post_number}</Badge>
                  {job.position_level && (
                    <Badge variant="secondary">{job.position_level}</Badge>
                  )}
                  <Badge variant="secondary" className="capitalize">
                    {job.contract_type.replace("_", " ")}
                  </Badge>
                  {job.is_active && (
                    <Badge className="bg-green-500 hover:bg-green-600">
                      Active
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="mt-3 text-sm text-gray-500">
              Deadline: {new Date(job.application_deadline).toLocaleDateString()}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
