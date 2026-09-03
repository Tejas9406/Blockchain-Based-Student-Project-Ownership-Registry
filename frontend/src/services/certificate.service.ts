import { API_BASE_URL, apiClient } from './api';
import { ApiResponse, CertificateMetadataData } from '../types';

export const certificateService = {
  /**
   * Retrieves certificate metadata for an anchored registration ID (GET /api/v1/certificates/{registrationId}).
   */
  async getCertificateMetadata(registrationId: string): Promise<CertificateMetadataData> {
    const response = await apiClient.get<ApiResponse<CertificateMetadataData>>(
      `/certificates/${registrationId}`
    );
    return response.data.data;
  },

  /**
   * Constructs the absolute URL for downloading the certificate PDF.
   */
  getCertificateDownloadUrl(registrationId: string): string {
    return `${API_BASE_URL}/certificates/${encodeURIComponent(registrationId)}/download`;
  },

  /**
   * Downloads the certificate PDF as a Blob.
   */
  async downloadCertificatePdf(registrationId: string): Promise<Blob> {
    const response = await apiClient.get(
      `/certificates/${registrationId}/download`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  /**
   * Constructs the QR code verification URL.
   */
  getCertificateQrUrl(registrationId: string): string {
    return `${API_BASE_URL}/certificates/${encodeURIComponent(registrationId)}/qr`;
  },
};
