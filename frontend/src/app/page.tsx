'use client';

import { ChangeEvent, DragEvent, useRef, useState } from 'react';
import HomeView from '../components/HomeView';
import PricingModal from '../components/PricingModal';
import ProcessingPage from '../components/ProcessingPage';
import {
  ProcessingMethod,
  ProcessingOptions,
  defaultProcessingOptions,
} from '../lib/processing';
import { PricingTab } from '../lib/pricing';

type PageState = 'home' | ProcessingMethod;

export default function Home() {
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPricingModal, setShowPricingModal] = useState(false);
  const [activeTab, setActiveTab] = useState<PricingTab>('包月会员');
  const [currentPage, setCurrentPage] = useState<PageState>('home');
  const [options, setOptions] = useState<ProcessingOptions>(defaultProcessingOptions);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadedImage(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProcessImage = () => {
    if (!uploadedImage || currentPage === 'home') return;

    setIsProcessing(true);
    setTimeout(() => {
      setProcessedImage(imagePreview);
      setIsProcessing(false);
    }, 2000);
  };

  const updateOptions = <T extends ProcessingMethod>(
    method: T,
    updates: Partial<ProcessingOptions[T]>
  ) => {
    setOptions((prev) => ({
      ...prev,
      [method]: { ...prev[method], ...updates },
    }));
  };

  const renderPricingModal = () =>
    showPricingModal ? (
      <PricingModal
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        onClose={() => setShowPricingModal(false)}
      />
    ) : null;

  if (currentPage !== 'home') {
    return (
      <>
        <ProcessingPage
          method={currentPage}
          imagePreview={imagePreview}
          processedImage={processedImage}
          isProcessing={isProcessing}
          hasUploadedImage={Boolean(uploadedImage)}
          options={options}
          updateOptions={updateOptions}
          onBack={() => setCurrentPage('home')}
          onOpenPricingModal={() => setShowPricingModal(true)}
          onProcessImage={handleProcessImage}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          fileInputRef={fileInputRef}
          onFileInputChange={handleImageUpload}
        />
        {renderPricingModal()}
      </>
    );
  }

  return (
    <>
      <HomeView
        onSelectMethod={(method) => {
          setCurrentPage(method);
          setProcessedImage(null);
        }}
        onOpenPricingModal={() => setShowPricingModal(true)}
      />
      {renderPricingModal()}
    </>
  );
}
